
# Proyecto de Extracción de Noticias RSS con Apache Airflow

## Propósito del Proyecto

Este proyecto tiene como objetivo la extracción y almacenamiento de noticias de diferentes fuentes RSS clasificadas por ideología (izquierda y derecha). Utiliza Apache Airflow para orquestar el flujo de trabajo de extracción y almacenamiento de datos en una base de datos PostgreSQL.

## Entorno de Desarrollo

El entorno de desarrollo está basado en Docker y Docker Compose para facilitar la configuración y despliegue de los servicios necesarios, incluyendo Airflow, PostgreSQL y Redis.

## Requisitos

- Docker
- Docker Compose

## Configuración Inicial

1. Clonar el repositorio:

    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd TNA_DATA
    ```

2. Crear un archivo `.env` en el directorio raíz del proyecto con las siguientes variables de entorno:

    ```env
    AIRFLOW_IMAGE_NAME=apache/airflow:2.10.4
    AIRFLOW_UID=50000
    AIRFLOW_PROJ_DIR=.
    _AIRFLOW_WWW_USER_USERNAME=airflow
    _AIRFLOW_WWW_USER_PASSWORD=airflow
    ```

3. Inicializar el entorno de Airflow:

    ```bash
    docker-compose up airflow-init
    ```

4. Levantar los servicios:

    ```bash
    docker-compose up
    ```

## Estructura del Proyecto

- `dags/`: Contiene los DAGs de Airflow.
- `logs/`: Directorio para los logs de Airflow.
- `config/`: Configuraciones adicionales de Airflow.
- `plugins/`: Plugins personalizados de Airflow.
- `variables.json`: Archivo JSON con las variables de configuración de las fuentes RSS.

## Descripción del DAG Principal

El DAG `extract_rss_dag.py` realiza las siguientes tareas:

1. Extrae noticias de fuentes RSS clasificadas por ideología (izquierda y derecha).
2. Almacena las noticias extraídas en una base de datos PostgreSQL, evitando duplicados.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o un pull request para discutir cualquier cambio que desees realizar.

## Licencia

Este proyecto está licenciado bajo la Licencia Apache 2.0. Consulta el archivo `LICENSE` para más detalles.

