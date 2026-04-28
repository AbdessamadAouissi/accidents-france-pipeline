"""DAG Airflow : pipeline complet accidents France.

Schedule : @daily (extraction incrémentale par année courante).
Stratégie : retry exponentiel, alerting via callback.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _alert_on_failure(context):
    """Callback en cas d'échec — point d'extension Slack/Email."""
    ti = context.get("task_instance")
    print(f"[ALERT] Task {ti.task_id} FAILED in DAG {ti.dag_id}")


default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "on_failure_callback": _alert_on_failure,
}


def run_extract_onisr():
    from src.extract import onisr  # noqa: WPS433
    onisr.run()


def run_extract_meteo():
    from src.extract import meteo  # noqa: WPS433
    meteo.run()


def run_extract_insee():
    from src.extract import insee  # noqa: WPS433
    insee.run()


def run_transform():
    from src.transform import run as t  # noqa: WPS433
    t.main()


def run_load():
    from src.load.duckdb_loader import load_all  # noqa: WPS433
    load_all()


def run_quality():
    from src.quality.run_checkpoints import main  # noqa: WPS433
    rc = main()
    if rc != 0:
        raise ValueError("Data Quality FAILED")


def run_ml():
    from src.ml.train_all import main  # noqa: WPS433
    main()


with DAG(
    dag_id="accidents_pipeline_daily",
    description="Pipeline complet : extract → validate → load → dbt → ML",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    tags=["accidents", "etl", "ml"],
) as dag:

    start = EmptyOperator(task_id="start")

    extract_onisr = PythonOperator(
        task_id="extract_onisr", python_callable=run_extract_onisr
    )
    extract_meteo = PythonOperator(
        task_id="extract_meteo", python_callable=run_extract_meteo
    )
    extract_insee = PythonOperator(
        task_id="extract_insee", python_callable=run_extract_insee
    )

    transform = PythonOperator(task_id="transform", python_callable=run_transform)
    load_duckdb = PythonOperator(task_id="load_duckdb", python_callable=run_load)
    validate = PythonOperator(task_id="validate_quality", python_callable=run_quality)

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {PROJECT_ROOT}/dbt_project && dbt run --profiles-dir .",
    )
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {PROJECT_ROOT}/dbt_project && dbt test --profiles-dir .",
    )

    train_ml = PythonOperator(task_id="train_ml", python_callable=run_ml)
    end = EmptyOperator(task_id="end")

    start >> [extract_onisr, extract_meteo, extract_insee] >> transform
    transform >> load_duckdb >> validate >> dbt_run >> dbt_test >> train_ml >> end
