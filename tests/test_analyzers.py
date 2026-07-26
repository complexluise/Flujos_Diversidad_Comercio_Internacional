"""Tests de EconomicDiversityAnalyzer."""

import pandas as pd
import pytest

from complex_trade_flow import EconomicDiversityAnalyzer
from complex_trade_flow.constants import EconomicComplexity
from complex_trade_flow.samples import (
    SAMPLE_YEAR,
    load_sample_network,
    sample_country_scheme,
    sample_data_path,
    sample_region_scheme,
)


@pytest.fixture(scope="module")
def network():
    return load_sample_network()


@pytest.fixture
def data_dir(tmp_path):
    """Copia los datos de ejemplo con el nombre que espera `from_year`."""
    origen = sample_data_path(f"cleaned_HS92_Y{SAMPLE_YEAR}_SAMPLE.csv")
    (tmp_path / f"cleaned_HS92_Y{SAMPLE_YEAR}_V202401b.csv").write_bytes(
        origen.read_bytes()
    )
    return tmp_path


def test_diversificacion_por_producto(network):
    resultado = EconomicDiversityAnalyzer.compute_entity_product_diversification(
        network, "South Asia", "by_region"
    )
    assert resultado["by_region"] == "South Asia"
    assert resultado["export_product_diversity"] > 1
    assert resultado["import_product_diversity"] > 1


def test_metricas_de_comercio_incluyen_masa(network):
    """
    Regresión: estas cuatro métricas fallaban siempre con KeyError: 'mass'
    porque el cargador no leía esa columna.
    """
    resultado = EconomicDiversityAnalyzer.compute_entity_trade_metrics(
        network, "South Asia", "by_region"
    )
    for clave in (
        "MASS_GAIN_IMPORTATION",
        "MASS_LOSS_EXPORTATION",
        "ENTROPY_MASS_LOSS_EXPORTATION",
        "ENTROPY_MASS_GAIN_IMPORTATION",
    ):
        assert clave in resultado
        assert resultado[clave] > 0


def test_la_entropia_de_masa_difiere_de_la_de_dinero(network):
    """
    Si ambas coincidieran, la métrica de masa no aportaría nada. Difieren
    porque el valor por tonelada cambia mucho entre materias primas y
    manufacturas.
    """
    resultado = EconomicDiversityAnalyzer.compute_entity_trade_metrics(
        network, "South Asia", "by_region"
    )
    assert resultado["ENTROPY_MASS_LOSS_EXPORTATION"] != pytest.approx(
        resultado["ENTROPY_MONEY_LOSS_EXPORTATION"]
    )


def test_analyze_year_devuelve_una_fila_por_entidad(data_dir):
    analyzer = EconomicDiversityAnalyzer(
        start_year=SAMPLE_YEAR,
        end_year=SAMPLE_YEAR,
        classification_schemes=[sample_region_scheme()],
    )
    df = analyzer.analyze_year(
        SAMPLE_YEAR,
        "by_region",
        EconomicComplexity.ENTITY_PRODUCT_DIVERSIFICATION,
        base_directory=str(data_dir),
    )
    assert len(df) == 7  # las siete regiones del Banco Mundial en el ejemplo
    assert "export_product_diversity" in df.columns


def test_run_analysis_escribe_el_csv(data_dir, tmp_path):
    salida = tmp_path / "salida"
    analyzer = EconomicDiversityAnalyzer(
        start_year=SAMPLE_YEAR,
        end_year=SAMPLE_YEAR,
        classification_schemes=[sample_region_scheme()],
    )
    analyzer.run_analysis(
        type_analysis=EconomicComplexity.ENTITY_PRODUCT_DIVERSIFICATION,
        output_directory=str(salida),
        base_directory=str(data_dir),
    )

    esperado = (
        salida
        / "compute_entity_product_diversification"
        / f"by_region_compute_entity_product_diversification_{SAMPLE_YEAR}.csv"
    )
    assert esperado.exists()
    assert len(pd.read_csv(esperado)) == 7


def test_las_economias_grandes_exportan_canastas_mas_diversas(network):
    """
    Comprobación de sentido sobre los datos de ejemplo: el generador incorpora
    este hecho estilizado, y sirve como test de humo de toda la cadena.
    """
    diversidad = {
        pais: EconomicDiversityAnalyzer.compute_entity_product_diversification(
            network, pais, "by_country"
        )["export_product_diversity"]
        for pais in ("USA", "CHN", "URY", "GHA")
    }
    assert diversidad["USA"] > diversidad["URY"]
    assert diversidad["CHN"] > diversidad["GHA"]
