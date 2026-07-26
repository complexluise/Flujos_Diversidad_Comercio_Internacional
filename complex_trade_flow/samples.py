"""
Acceso a los datos de ejemplo que se distribuyen con el paquete.

Los datos son SINTÉTICOS: sirven para probar la librería sin descargar nada, no
para sacar conclusiones sobre comercio. Ver `sample_data/README.md`.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

import pandas as pd

from .networks import TradeNetwork
from .utils import ClassificationScheme

SAMPLE_YEAR = 2020

__all__ = [
    "SAMPLE_YEAR",
    "sample_data_path",
    "load_sample_trade_data",
    "sample_region_scheme",
    "sample_country_scheme",
    "load_sample_network",
]


def sample_data_path(filename: str) -> Path:
    """
    Devuelve la ruta en disco de un archivo del dataset de ejemplo.

    Funciona tanto con el repositorio clonado como con el paquete instalado
    desde una wheel.
    """
    return Path(str(resources.files("complex_trade_flow") / "sample_data" / filename))


def load_sample_trade_data() -> pd.DataFrame:
    """
    Carga los flujos de comercio sintéticos del año de ejemplo.

    Returns:
        pd.DataFrame: columnas `year`, `exporter_iso_code_3`,
        `importer_iso_code_3`, `product_category_code`, `money` y `mass`.
    """
    return pd.read_csv(sample_data_path(f"cleaned_HS92_Y{SAMPLE_YEAR}_SAMPLE.csv"))


def sample_region_scheme() -> ClassificationScheme:
    """Esquema que agrupa los países de ejemplo por región del Banco Mundial."""
    return ClassificationScheme(
        name="by_region",
        file_path=str(sample_data_path("countries_SAMPLE.csv")),
        key_column="id",
        value_column="region.value",
    )


def sample_country_scheme() -> ClassificationScheme:
    """Esquema sin agrupación: cada país es su propia entidad."""
    return ClassificationScheme(name="by_country")


def load_sample_network(
    classification_schemes: list[ClassificationScheme] | None = None,
) -> TradeNetwork:
    """
    Construye una `TradeNetwork` lista para usar con los datos de ejemplo.

    Args:
        classification_schemes: esquemas a aplicar. Por defecto usa el esquema
            regional y el de país.

    Returns:
        TradeNetwork: red de comercio del año de ejemplo.
    """
    if classification_schemes is None:
        classification_schemes = [sample_region_scheme(), sample_country_scheme()]
    return TradeNetwork(
        trade_data=load_sample_trade_data(),
        classification_schemes=classification_schemes,
    )
