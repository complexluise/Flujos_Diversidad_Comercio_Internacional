# 🌍 complex_trade_flow

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Licencia](https://img.shields.io/badge/license-MIT-green)

**¿A cuántos productos equivale realmente la canasta exportadora de un país?**

`complex_trade_flow` mide la **diversidad efectiva de productos** en la red del
comercio internacional, y permite agregar países en las entidades que quieras
—regiones, niveles de ingreso, norte/sur— para comparar su diversidad a lo largo
del tiempo.

Un país puede exportar 100 productos distintos y aun así concentrar el 95% del
valor en uno solo. El conteo dice 100; la diversidad efectiva dice ~1. Esa
distinción es lo que esta librería calcula.

## ⚡ Pruébalo en 30 segundos

No necesitas descargar datos ni registrarte en ninguna parte:

```bash
pip install complex-trade-flow
python -m complex_trade_flow.demo
```

El demo usa un dataset **sintético** incluido en el paquete. Para análisis reales
ver [Datos reales](#-datos-reales).

## 📊 Uso

Todos los ejemplos de abajo se ejecutan en CI, así que si los lees acá es porque
funcionan.

```python
from complex_trade_flow import DiversityCalculator, load_sample_network

red = load_sample_network()

# Diversidad de exportaciones del sur de Asia
sur_de_asia = red.filter_data_by_entities(
    scheme_name="by_region",
    exporters=["South Asia"],
)
diversidad = DiversityCalculator.calculate_diversity_index(data=sur_de_asia)
print(f"Diversidad de exportaciones del sur de Asia: {diversidad:.1f}")
```

### Definir tus propias entidades

Un esquema de clasificación es un CSV con dos columnas: el código ISO-3 del país
y el grupo al que pertenece. Con eso puedes agrupar el mundo como quieras.

```python
import pandas as pd
from complex_trade_flow import ClassificationScheme, TradeNetwork, DiversityCalculator
from complex_trade_flow.samples import load_sample_trade_data, sample_data_path

# Un esquema propio: norte y sur global
paises = pd.read_csv(sample_data_path("countries_SAMPLE.csv"))
norte = {"USA", "CAN", "DEU", "FRA", "GBR", "ITA", "ESP", "NLD", "SWE", "JPN", "AUS"}
paises["grupo"] = paises["id"].apply(lambda c: "Norte" if c in norte else "Sur")
paises.to_csv("/tmp/norte_sur.csv", index=False)

esquema = ClassificationScheme(
    name="norte_sur",
    file_path="/tmp/norte_sur.csv",
    key_column="id",
    value_column="grupo",
)

red = TradeNetwork(
    trade_data=load_sample_trade_data(),
    classification_schemes=[esquema],
)

for grupo in ["Norte", "Sur"]:
    datos = red.filter_data_by_entities(scheme_name="norte_sur", exporters=[grupo])
    indice = DiversityCalculator.calculate_diversity_index(data=datos)
    print(f"{grupo}: {indice:.1f} productos efectivos")
```

### Diversidad por masa, no solo por dinero

La misma canasta se ve distinta si la pesas en dólares o en toneladas. Las
materias primas pesan mucho por dólar; las manufacturas casi nada.

```python
from complex_trade_flow import DiversityCalculator, load_sample_network

red = load_sample_network()
datos = red.filter_data_by_entities(scheme_name="by_region", exporters=["North America"])

por_dinero = DiversityCalculator.calculate_diversity_index(data=datos, column="money")
por_masa = DiversityCalculator.calculate_diversity_index(data=datos, column="mass")
print(f"Diversidad por valor: {por_dinero:.1f} | por masa: {por_masa:.1f}")
```

## 🧮 La métrica

El índice es el **número de Hill de orden 1**:

$$D = 2^{H} \quad \text{donde} \quad H = -\sum_i p_i \log_2 p_i$$

donde $p_i$ es la fracción del valor total (o de la masa total) que corresponde
al producto $i$. Es decir, la exponencial de la entropía de Shannon.

La propiedad que lo hace útil es el **principio de duplicación**: si el índice
vale 20, la canasta se comporta como si tuviera 20 productos de igual peso. Eso
lo hace directamente comparable e interpretable, a diferencia de la entropía en
bits.

Referencias: [Hill (1973)](https://doi.org/10.2307/1934352),
[Jost (2006)](https://doi.org/10.1111/j.2006.0030-1299.14714.x).

**Qué NO es esto**: no es el Índice de Complejidad Económica (ECI) ni el PCI de
Hidalgo y Hausmann. No hay ventaja comparativa revelada ni espacio de producto.
Si buscas eso, [`py-ecomplexity`](https://github.com/cid-harvard/py-ecomplexity)
o el paquete de R [`economiccomplexity`](https://pacha.dev/economiccomplexity/)
son las herramientas adecuadas. Lo que aporta esta librería y no está empaquetado
en otro lado es la **agregación flexible de países** en entidades arbitrarias.

## 🌐 Datos reales

Los datos reales no se distribuyen con el paquete: BACI son varios GB y requieren
registro en CEPII.

1. **BACI** (CEPII) — descarga la versión HS92 desde
   [su sitio](http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37)
   y coloca en `data/raw_data/BACI_HS92_V202401b/`:
   - `BACI_HS92_Y{año}_V202401b.csv` para cada año
   - `country_codes_V202401b.csv`
2. **Banco Mundial** — en `data/raw_data/world_bank_data/`:
   - `countries.csv` (países y regiones)
   - `NY.GDP.DEFL.ZS.AD_1995-2023.csv` (deflactor del PIB)

Copia `.env.example` a `.env` y ajusta las rutas. Luego:

```python
# requiere-datos-reales
from complex_trade_flow.clean_trade_data import DataCleaner
from complex_trade_flow import TradeNetwork

DataCleaner.clean_trade_data()

red = TradeNetwork.from_year(2020, base_directory="data/processed_data/BACI_HS92_V202401b/cleaned_trade_data/")
```

La limpieza convierte los valores a USD constantes usando el deflactor del PIB.

### Análisis multi-año

```python
# requiere-datos-reales
from complex_trade_flow import ClassificationScheme, EconomicDiversityAnalyzer
from complex_trade_flow.constants import EconomicComplexity

esquema = ClassificationScheme(
    name="by_region",
    file_path="data/raw_data/world_bank_data/countries.csv",
    key_column="id",
    value_column="region.value",
)

EconomicDiversityAnalyzer(
    start_year=1995,
    end_year=2022,
    classification_schemes=[esquema],
).run_analysis(
    type_analysis=EconomicComplexity.ENTITY_PRODUCT_DIVERSIFICATION,
    output_directory="data/processed_data/BACI_HS92_V202401b/by_region/",
    base_directory="data/processed_data/BACI_HS92_V202401b/cleaned_trade_data/",
)
```

## 📈 App

Hay una app en Streamlit que explora los resultados ya calculados (1995–2022,
235 países), en `app/main.py`:

```bash
pip install "complex-trade-flow[app]"
streamlit run app/main.py
```

## 🛠 Desarrollo

```bash
git clone https://github.com/complexluise/complex_trade_flow.git
cd complex_trade_flow
pip install -e ".[dev]"
pytest
```

Para regenerar el dataset sintético de ejemplo (determinista):

```bash
python scripts/generate_sample_data.py
```

## 🗺 Estado del proyecto

Este repositorio pasó por una reevaluación honesta de qué funciona y qué no; el
resultado está en [`docs/EVALUACION.md`](docs/EVALUACION.md), incluyendo lo que
falta por hacer. Contribuciones bienvenidas — las
[issues abiertas](https://github.com/complexluise/complex_trade_flow/issues) son
un buen punto de partida.

## 🙏 Agradecimientos

- A **GEINCyR**, por brindar un espacio de aprendizaje y discusión de la
  complejidad no solo desde lo técnico sino como un cambio de visión de mundo.
- A **BACI-CEPII** por los datos de comercio internacional.
- Al **Banco Mundial** por los indicadores económicos.

## Licencia

MIT — ver [LICENSE](LICENSE).
