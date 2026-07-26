"""Tests de TradeNetwork, ClassificationScheme y el cargador de datos."""

import pandas as pd
import pytest

from complex_trade_flow import ClassificationScheme, TradeNetwork, TradeDataLoader
from complex_trade_flow.samples import (
    SAMPLE_YEAR,
    load_sample_network,
    load_sample_trade_data,
    sample_country_scheme,
    sample_data_path,
    sample_region_scheme,
)


@pytest.fixture(scope="module")
def network() -> TradeNetwork:
    return load_sample_network()


def test_los_datos_de_ejemplo_traen_todas_las_columnas():
    data = load_sample_trade_data()
    esperadas = {
        "year", "exporter_iso_code_3", "importer_iso_code_3",
        "product_category_code", "money", "mass",
    }
    assert esperadas <= set(data.columns)
    assert len(data) > 0
    assert (data["year"] == SAMPLE_YEAR).all()


def test_clasificar_no_pierde_ni_duplica_filas(network):
    assert network.trade_data_classified.shape[0] == network.trade_data.shape[0]


def test_se_crean_las_columnas_de_clasificacion(network):
    for columna in ("by_region_importer", "by_region_exporter"):
        assert columna in network.trade_data_classified.columns


def test_las_entidades_regionales_son_regiones(network):
    entidades = network.entities["by_region"]
    assert "Latin America & Caribbean" in entidades
    assert "COL" not in entidades


def test_sin_clasificacion_cada_pais_es_su_propia_entidad(network):
    assert network.entities["by_country"] == network.countries


def test_filtrar_por_entidad_devuelve_solo_esa_entidad(network):
    data = network.filter_data_by_entities(
        scheme_name="by_region", exporters=["South Asia"]
    )
    assert len(data) > 0
    assert set(data["by_region_exporter"].unique()) == {"South Asia"}


def test_filtrar_sin_argumentos_devuelve_todo(network):
    completo = network.filter_data_by_entities(scheme_name="by_region")
    assert len(completo) == len(network.trade_data_classified)


def test_pais_no_listado_queda_como_unknown():
    esquema = sample_region_scheme()
    clasificacion = esquema.apply_classification({"COL", "XXX"})
    assert clasificacion["COL"] == "Latin America & Caribbean"
    assert clasificacion["XXX"] == "Unknown"


def test_esquema_sin_archivo_mapea_cada_pais_a_si_mismo():
    esquema = sample_country_scheme()
    assert esquema.apply_classification({"COL", "USA"}) == {"COL": "COL", "USA": "USA"}


def test_from_year_carga_la_columna_mass(tmp_path):
    """
    Regresión: `usecols` omitía `mass`, así que todas las métricas de masa
    fallaban con KeyError al llegar por `from_year`.
    """
    origen = sample_data_path(f"cleaned_HS92_Y{SAMPLE_YEAR}_SAMPLE.csv")
    destino = tmp_path / f"cleaned_HS92_Y{SAMPLE_YEAR}_V202401b.csv"
    destino.write_bytes(origen.read_bytes())

    red = TradeNetwork.from_year(
        SAMPLE_YEAR,
        base_directory=str(tmp_path),
        classification_schemes=[sample_country_scheme()],
    )
    assert "mass" in red.trade_data.columns
    assert red.trade_data["mass"].sum() > 0


def test_el_cargador_avisa_si_falta_el_archivo(tmp_path):
    loader = TradeDataLoader(str(tmp_path))
    with pytest.raises(FileNotFoundError, match="No se encontró"):
        loader.load_trade_data(1800)


def test_el_cargador_avisa_si_faltan_columnas(tmp_path):
    incompleto = tmp_path / "cleaned_HS92_Y2020_V202401b.csv"
    pd.DataFrame({"year": [2020], "money": [1.0]}).to_csv(incompleto, index=False)

    loader = TradeDataLoader(str(tmp_path))
    with pytest.raises(ValueError, match="faltan las columnas"):
        loader.load_trade_data(2020)


def test_plantilla_de_nombre_configurable(tmp_path):
    archivo = tmp_path / "mis_datos_2020.csv"
    load_sample_trade_data().to_csv(archivo, index=False)

    loader = TradeDataLoader(str(tmp_path), filename_template="mis_datos_{year}.csv")
    assert len(loader.load_trade_data(2020)) > 0


def test_red_sin_esquemas_no_expone_entidades():
    red = TradeNetwork(trade_data=load_sample_trade_data())
    assert len(red.countries) > 0
    assert not hasattr(red, "entities")
