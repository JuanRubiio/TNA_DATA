from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import feedparser
from datetime import datetime
from airflow.models import Variable

# Definir fuentes RSS
RSS_FEEDS = Variable.get("periodicos", deserialize_json=True)

# Función para extraer noticias
def extraer_noticias(**kwargs):
    noticias = []
    for fuente, data in RSS_FEEDS.items():
        if data["enabled"]:
            feed = feedparser.parse(data["url"])
            for entrada in feed.entries:
                noticia = {
                    "titulo": entrada.title,
                    "descripcion": entrada.summary,
                    "fecha_publicacion": entrada.published if "published" in entrada else None,
                    "enlace": entrada.link,
                    "medio": fuente,
                    "autor": entrada.get("author", None),
                    "categorias": [categoria.term for categoria in entrada.get("tags", [])],
                    "imagen_url": entrada.get("media_content", [{}])[0].get("url", None),
                    "imagen_ancho": entrada.get("media_content", [{}])[0].get("width", None),
                    "imagen_alto": entrada.get("media_content", [{}])[0].get("height", None),
                    "thumbnail_url": entrada.get("media_thumbnail", [{}])[0].get("url", None),
                    "thumbnail_ancho": entrada.get("media_thumbnail", [{}])[0].get("width", None),
                    "thumbnail_alto": entrada.get("media_thumbnail", [{}])[0].get("height", None),
                }
                noticias.append(noticia)
    return noticias

# Función para visualizar noticias
def visualizar_noticias(**kwargs):
    noticias = kwargs["ti"].xcom_pull(task_ids="extraer_noticias")
    if not noticias:
        return

    for noticia in noticias:
        print(f"Título: {noticia['titulo']}")
        print(f"Descripción: {noticia['descripcion']}")
        print(f"Fecha de Publicación: {noticia['fecha_publicacion']}")
        print(f"Enlace: {noticia['enlace']}")
        print(f"Medio: {noticia['medio']}")
        print(f"Autor: {noticia['autor']}")
        print(f"Categorías: {', '.join(noticia['categorias'])}")
        print("-" * 80)

# Función para almacenar noticias en PostgreSQL
def almacenar_noticias(**kwargs):
    noticias = kwargs["ti"].xcom_pull(task_ids="extraer_noticias")
    if not noticias:
        return

    execution_date = kwargs["execution_date"].isoformat()  # Convert to ISO format string

    pg_hook = PostgresHook(postgres_conn_id="postgres_conn")
    conn = pg_hook.get_conn()
    cursor = conn.cursor()
 
    try:
        # Insertar noticias evitando duplicados
        for noticia in noticias:
            cursor.execute("""
                INSERT INTO tna.noticias (titulo, descripcion, fecha_publicacion, enlace, medio, autor, categorias, imagen_url, imagen_ancho, imagen_alto, thumbnail_url, thumbnail_ancho, thumbnail_alto, fecha_ejecucion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (enlace) DO NOTHING;
            """, (
                noticia["titulo"], noticia["descripcion"], noticia["fecha_publicacion"], noticia["enlace"], noticia["medio"],
                noticia["autor"], noticia["categorias"] if noticia["categorias"] else '{}', noticia["imagen_url"], noticia["imagen_ancho"], noticia["imagen_alto"],
                noticia["thumbnail_url"], noticia["thumbnail_ancho"], noticia["thumbnail_alto"], execution_date
            ))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Error al almacenar noticias: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def eliminar_noticias(**kwargs):
    pg_hook = PostgresHook(postgres_conn_id="postgres_conn")
    conn = pg_hook.get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        DROP TABLE IF EXISTS tna.noticias;
    """)
    conn.commit()
    cursor.close()
    conn.close()

def recrear_tablas(**kwargs):
    pg_hook = PostgresHook(postgres_conn_id="postgres_conn")
    conn = pg_hook.get_conn()
    cursor = conn.cursor()
    # Creamos el esquema si no existe
    cursor.execute("""
        CREATE SCHEMA IF NOT EXISTS tna;
    """)

    # Crear tabla si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tna.noticias (
            id SERIAL PRIMARY KEY,
            titulo TEXT,
            descripcion TEXT,
            fecha_publicacion TIMESTAMP,
            enlace TEXT UNIQUE,
            medio TEXT,
            autor TEXT,
            categorias TEXT[],
            imagen_url TEXT,
            imagen_ancho INT,
            imagen_alto INT,
            thumbnail_url TEXT,
            thumbnail_ancho INT,
            thumbnail_alto INT,
            fecha_ejecucion TIMESTAMP
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()

# Definir el DAG
with DAG(
    dag_id="obtener_noticias",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args={"owner": "TNA", "retries": 1},
) as dag:

    # Crear tareas
    tarea_extraer = PythonOperator(
        task_id="extraer_noticias",
        python_callable=extraer_noticias,
        provide_context=True,
    )

    tarea_visualizar = PythonOperator(
        task_id="visualizar_noticias",
        python_callable=visualizar_noticias,
        provide_context=True,
    )
    
    tarea_eliminar = PythonOperator(
        task_id="eliminar_noticias",
        python_callable=eliminar_noticias,
        provide_context=True,
    )  
    
    tarea_recrear = PythonOperator(
        task_id="recrear_tablas",
        python_callable=recrear_tablas,
        provide_context=True,
    )

    tarea_almacenar = PythonOperator(
        task_id="almacenar_noticias",
        python_callable=almacenar_noticias,
        provide_context=True,
    )

    # Definir la dependencia de tareas
    tarea_extraer >> tarea_visualizar >> tarea_eliminar >> tarea_recrear >> tarea_almacenar
