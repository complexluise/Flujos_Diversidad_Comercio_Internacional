"""
Genera el dataset sintético de ejemplo que se distribuye con el paquete.

IMPORTANTE: los datos que produce este script NO son datos de comercio reales.
Son datos sintéticos con la *forma* de BACI-CEPII ya limpio, generados para que
`python -m complex_trade_flow.demo` y la suite de tests funcionen sin descargar
nada. No deben usarse para sacar conclusiones sustantivas sobre comercio.

El generador es determinista (semilla fija), así que el CSV versionado en el
repositorio se puede regenerar y verificar byte a byte:

    python scripts/generate_sample_data.py

Modelo generativo (deliberadamente simple, documentado para que se pueda auditar):

1. Cada país tiene un "tamaño" tomado de su PIB nominal 2020 aproximado.
2. Cada país tiene un conjunto de capacidades: cuántos productos sabe exportar,
   correlacionado con su tamaño. Esto reproduce el hecho estilizado de que las
   economías grandes exportan canastas más diversas.
3. Los flujos siguen una gravedad simple: valor ~ tamaño_exportador *
   tamaño_importador / distancia_entre_regiones.
4. Dentro de la canasta de un país los valores siguen una ley de potencias
   (Zipf), que es lo que hace que la diversidad efectiva sea bastante menor que
   el conteo crudo de productos — el fenómeno que la librería mide.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20260726
YEAR = 2020

# 42 países reales, con su región del Banco Mundial y un tamaño económico
# aproximado (PIB nominal 2020 en billones de USD, redondeado). El tamaño se usa
# solo para dar un orden de magnitud plausible a los flujos: si se sortea al azar
# salen resultados absurdos, como Ghana siendo el exportador más diversificado
# del mundo. No es un dato del que se deba depender — es escala, no medición.
COUNTRIES: dict[str, tuple[str, float]] = {
    "COL": ("Latin America & Caribbean", 0.27),
    "BRA": ("Latin America & Caribbean", 1.45),
    "MEX": ("Latin America & Caribbean", 1.09),
    "ARG": ("Latin America & Caribbean", 0.39),
    "CHL": ("Latin America & Caribbean", 0.25),
    "PER": ("Latin America & Caribbean", 0.20),
    "ECU": ("Latin America & Caribbean", 0.10),
    "URY": ("Latin America & Caribbean", 0.05),
    "USA": ("North America", 21.06),
    "CAN": ("North America", 1.65),
    "DEU": ("Europe & Central Asia", 3.89),
    "FRA": ("Europe & Central Asia", 2.63),
    "GBR": ("Europe & Central Asia", 2.71),
    "ITA": ("Europe & Central Asia", 1.90),
    "ESP": ("Europe & Central Asia", 1.28),
    "NLD": ("Europe & Central Asia", 0.91),
    "POL": ("Europe & Central Asia", 0.60),
    "TUR": ("Europe & Central Asia", 0.72),
    "RUS": ("Europe & Central Asia", 1.49),
    "SWE": ("Europe & Central Asia", 0.54),
    "CHN": ("East Asia & Pacific", 14.72),
    "JPN": ("East Asia & Pacific", 5.06),
    "KOR": ("East Asia & Pacific", 1.64),
    "IDN": ("East Asia & Pacific", 1.06),
    "THA": ("East Asia & Pacific", 0.50),
    "VNM": ("East Asia & Pacific", 0.34),
    "MYS": ("East Asia & Pacific", 0.34),
    "AUS": ("East Asia & Pacific", 1.33),
    "IND": ("South Asia", 2.67),
    "PAK": ("South Asia", 0.26),
    "BGD": ("South Asia", 0.37),
    "LKA": ("South Asia", 0.08),
    "ZAF": ("Sub-Saharan Africa", 0.34),
    "NGA": ("Sub-Saharan Africa", 0.43),
    "KEN": ("Sub-Saharan Africa", 0.10),
    "ETH": ("Sub-Saharan Africa", 0.10),
    "GHA": ("Sub-Saharan Africa", 0.07),
    "EGY": ("Middle East & North Africa", 0.36),
    "MAR": ("Middle East & North Africa", 0.11),
    "SAU": ("Middle East & North Africa", 0.70),
    "ARE": ("Middle East & North Africa", 0.36),
    "ISR": ("Middle East & North Africa", 0.41),
}

REGION = {code: region for code, (region, _) in COUNTRIES.items()}
GDP = {code: gdp for code, (_, gdp) in COUNTRIES.items()}

# Capítulos HS92 reales; los códigos de 6 dígitos se derivan de ellos.
HS_CHAPTERS = [1, 3, 9, 10, 15, 22, 26, 27, 39, 44, 52, 61, 62, 64, 72, 73,
               84, 85, 87, 90, 94]
PRODUCTS_PER_CHAPTER = 6

# Distancia relativa entre regiones (1.0 = misma región).
REGION_DISTANCE = {
    ("Latin America & Caribbean", "North America"): 1.4,
    ("Latin America & Caribbean", "Europe & Central Asia"): 2.2,
    ("Latin America & Caribbean", "East Asia & Pacific"): 2.6,
    ("North America", "Europe & Central Asia"): 1.8,
    ("North America", "East Asia & Pacific"): 2.1,
    ("Europe & Central Asia", "East Asia & Pacific"): 2.0,
    ("South Asia", "East Asia & Pacific"): 1.5,
    ("Sub-Saharan Africa", "Europe & Central Asia"): 1.9,
    ("Middle East & North Africa", "Europe & Central Asia"): 1.5,
}


def region_distance(a: str, b: str) -> float:
    if a == b:
        return 1.0
    return REGION_DISTANCE.get((a, b)) or REGION_DISTANCE.get((b, a)) or 2.4


def build_products() -> list[int]:
    return [
        chapter * 10_000 + 100 * (i + 1) + 10
        for chapter in HS_CHAPTERS
        for i in range(PRODUCTS_PER_CHAPTER)
    ]


def generate() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    codes = list(COUNTRIES)
    products = build_products()

    # 1. Tamaño económico, normalizado para que la mediana valga 1.
    median_gdp = float(np.median(list(GDP.values())))
    sizes = {code: GDP[code] / median_gdp for code in codes}

    # 2. Capacidades: los países grandes exportan más variedad de productos.
    max_size = max(sizes.values())
    capabilities: dict[str, np.ndarray] = {}
    for code in codes:
        share = 0.12 + 0.75 * (sizes[code] / max_size) ** 0.5
        n = max(3, int(round(share * len(products))))
        capabilities[code] = rng.choice(products, size=n, replace=False)

    # 3-4. Flujos con gravedad y valores Zipf dentro de cada canasta.
    rows = []
    for exporter in codes:
        basket = capabilities[exporter]
        # Ley de potencias sobre la canasta: pocos productos concentran el valor.
        # El exponente decrece con el tamaño de la economía, de modo que las
        # economías grandes tienen canastas más planas (y por tanto diversidad
        # efectiva más alta) y las pequeñas concentran su valor en pocos
        # productos. Sin esto el orden entre países queda dominado por el ruido.
        concentration = 1.75 - 0.95 * (sizes[exporter] / max_size) ** 0.5
        ranks = np.arange(1, len(basket) + 1)
        weights = 1.0 / ranks ** (concentration * rng.uniform(0.9, 1.1))
        weights = weights / weights.sum()
        shuffled = rng.permutation(len(basket))
        basket, weights = basket[shuffled], weights[shuffled]

        for importer in codes:
            if exporter == importer:
                continue
            pull = (
                sizes[exporter] * sizes[importer]
                / region_distance(REGION[exporter], REGION[importer]) ** 1.8
            )
            # No todos los productos de la canasta llegan a todos los destinos.
            traded = rng.random(len(basket)) < np.clip(0.10 + 0.55 * pull, 0.05, 0.85)
            if not traded.any():
                continue
            for product, weight in zip(basket[traded], weights[traded]):
                money = pull * weight * 1e6 * rng.lognormal(0.0, 0.45)
                if money < 1.0:
                    continue
                # La masa se relaciona con el valor pero con densidad de valor
                # distinta por capítulo: materias primas pesan mucho más por dólar.
                chapter = product // 10_000
                value_density = 0.04 if chapter <= 27 else 1.8
                mass = money / value_density * rng.lognormal(0.0, 0.35)
                rows.append((YEAR, exporter, importer, int(product),
                             round(money, 2), round(mass, 2)))

    df = pd.DataFrame(rows, columns=[
        "year", "exporter_iso_code_3", "importer_iso_code_3",
        "product_category_code", "money", "mass",
    ])
    return df.sort_values(
        ["exporter_iso_code_3", "importer_iso_code_3", "product_category_code"]
    ).reset_index(drop=True)


def main() -> None:
    out_dir = Path(__file__).resolve().parents[1] / "complex_trade_flow" / "sample_data"
    out_dir.mkdir(parents=True, exist_ok=True)

    trade = generate()
    trade_path = out_dir / f"cleaned_HS92_Y{YEAR}_SAMPLE.csv"
    trade.to_csv(trade_path, index=False)

    countries = pd.DataFrame(
        {"id": list(COUNTRIES), "region.value": [REGION[c] for c in COUNTRIES]}
    )
    countries.to_csv(out_dir / "countries_SAMPLE.csv", index=False)

    size_kb = trade_path.stat().st_size / 1024
    print(f"Escrito {trade_path} ({len(trade):,} filas, {size_kb:,.0f} KB)")
    print(f"Escrito {out_dir / 'countries_SAMPLE.csv'} ({len(countries)} países)")


if __name__ == "__main__":
    main()
