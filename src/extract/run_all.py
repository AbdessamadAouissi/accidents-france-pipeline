"""Orchestration locale (sans Airflow) — exécute toutes les extractions."""

from src.extract import insee, meteo, onisr
from src.utils.logger import get_logger

log = get_logger(__name__)


def main() -> None:
    log.info("======== EXTRACT (run_all) ========")
    meteo.run()
    insee.run()
    onisr.run()
    log.info("======== EXTRACT terminé ========")


if __name__ == "__main__":
    main()
