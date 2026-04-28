"""Helpers d'I/O : détection d'encodage, lecture robuste de CSV."""

from pathlib import Path

import chardet
import pandas as pd

from src.utils.logger import get_logger

log = get_logger(__name__)


def detect_encoding(path: Path, sample_size: int = 100_000) -> str:
    """Détecte l'encodage d'un fichier (ONISR utilise souvent latin-1 / cp1252)."""
    with open(path, "rb") as f:
        raw = f.read(sample_size)
    result = chardet.detect(raw)
    enc = result.get("encoding") or "utf-8"
    log.debug(f"Encodage détecté pour {path.name}: {enc} (conf={result.get('confidence'):.2f})")
    return enc


def read_csv_robust(
    path: Path,
    sep: str = ";",
    dtype: dict | None = None,
    **kwargs,
) -> pd.DataFrame:
    """Lit un CSV avec détection automatique de l'encodage et fallback."""
    encodings = [detect_encoding(path), "utf-8", "latin-1", "cp1252"]
    last_err: Exception | None = None
    for enc in dict.fromkeys(encodings):
        try:
            df = pd.read_csv(path, sep=sep, encoding=enc, dtype=dtype, low_memory=False, **kwargs)
            log.info(f"✓ {path.name} lu ({len(df):,} lignes, encoding={enc})")
            return df
        except (UnicodeDecodeError, pd.errors.ParserError) as e:
            last_err = e
            continue
    raise RuntimeError(f"Impossible de lire {path}: {last_err}")


def save_parquet(df: pd.DataFrame, path: Path) -> None:
    """Sauvegarde un DataFrame en Parquet (compression snappy)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, engine="pyarrow", compression="snappy", index=False)
    log.info(f"✓ Parquet sauvé : {path} ({len(df):,} lignes)")
