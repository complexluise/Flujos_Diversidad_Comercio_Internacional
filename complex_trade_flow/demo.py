"""
Demo ejecutable de la librería.

    python -m complex_trade_flow.demo

Corre en segundos, sin descargar nada, usando el dataset sintético incluido.
El objetivo es que cualquiera vea un resultado antes de decidir si le interesa
conseguir los datos reales.
"""

from __future__ import annotations

import pandas as pd

from .diversity_metrics import DiversityCalculator
from .samples import SAMPLE_YEAR, load_sample_network

BAR_WIDTH = 34


def _bar(value: float, largest: float, width: int = BAR_WIDTH) -> str:
    filled = 0 if largest <= 0 else int(round(width * value / largest))
    return "█" * filled


def _rule(title: str) -> None:
    print(f"\n{title}\n{'─' * 72}")


def diversity_by(network, scheme_name: str, role: str) -> pd.Series:
    """
    Diversidad efectiva de productos de cada entidad de un esquema.

    Args:
        network: la red de comercio.
        scheme_name: nombre del esquema de clasificación.
        role: "exporters" o "importers".

    Returns:
        pd.Series: diversidad por entidad, ordenada de mayor a menor.
    """
    scores = {
        entity: DiversityCalculator.calculate_diversity_index(
            data=network.filter_data_by_entities(
                scheme_name=scheme_name, **{role: [entity]}
            )
        )
        for entity in sorted(network.entities[scheme_name])
    }
    return pd.Series(scores).sort_values(ascending=False)


def main() -> None:
    print("complex_trade_flow — demo")
    print("=" * 72)
    print("ATENCIÓN: los datos de este demo son SINTÉTICOS, no son comercio real.")
    print("Sirven para mostrar cómo funciona la librería. Ver sample_data/README.md")

    network = load_sample_network()
    print(
        f"\nRed de ejemplo del año {SAMPLE_YEAR}: "
        f"{len(network.countries)} países, {len(network.products)} productos, "
        f"{len(network.trade_data):,} flujos."
    )

    _rule("¿Qué mide esta librería?")
    print(
        "La diversidad efectiva de productos: a cuántos productos EQUIVALE la\n"
        "canasta de un país, si todos pesaran lo mismo. Es 2^H, el número de Hill\n"
        "de orden 1. Un país que exporta 100 productos pero concentra el 95% del\n"
        "valor en uno solo tiene una diversidad cercana a 1, no a 100."
    )

    export_by_country = diversity_by(network, "by_country", "exporters")
    largest = float(export_by_country.iloc[0])
    n_products = len(network.products)

    _rule(f"Diversidad de EXPORTACIONES por país (máximo posible: {n_products})")
    for code, value in export_by_country.head(5).items():
        print(f"  {code}  {value:7.1f}  {_bar(float(value), largest)}")
    print(f"  {'...':>3}")
    for code, value in export_by_country.tail(3).items():
        print(f"  {code}  {value:7.1f}  {_bar(float(value), largest)}")

    export_by_region = diversity_by(network, "by_region", "exporters")
    import_by_region = diversity_by(network, "by_region", "importers")
    largest_region = float(export_by_region.iloc[0])

    _rule("Agregando países en regiones (lo que distingue a esta librería)")
    print(f"  {'región':<28}{'export':>8}{'import':>8}")
    for region, value in export_by_region.items():
        print(
            f"  {region:<28}{value:8.1f}{import_by_region[region]:8.1f}  "
            f"{_bar(float(value), largest_region, 22)}"
        )
    print(
        "\n  Las mismas entidades se pueden definir por nivel de ingreso, por\n"
        "  norte/sur, o como quieras: basta un CSV con dos columnas."
    )

    _rule("Siguiente paso")
    print(
        "  Con datos reales de BACI-CEPII:\n\n"
        "      from complex_trade_flow import TradeNetwork, ClassificationScheme\n"
        "      red = TradeNetwork.from_year(2020, base_directory='ruta/a/tus/datos')\n\n"
        "  Ver la sección 'Datos reales' del README."
    )


if __name__ == "__main__":
    main()
