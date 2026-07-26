# Reevaluación del repositorio — julio 2026

Evaluación del estado de `complex_trade_flow` desde la perspectiva de **alguien que
no eres tú**: qué encuentra, qué puede correr, y por qué hoy no lo usa nadie.

Todo lo que se afirma abajo como "verificado" se comprobó ejecutando el código en un
entorno limpio (Python 3.11, dependencias instaladas desde cero, datos sintéticos con
la forma de BACI ya limpio). No es lectura de código: es ejecución.

---

## 1. Veredicto

**El núcleo científico está bien. La superficie de usuario no existe.**

Hay exactamente una cosa en este repositorio que funciona, está validada y vale la
pena: el cálculo de diversidad como *número efectivo de productos*
(`2^H`, número de Hill de orden 1) aplicado a flujos de comercio, con una capa de
clasificación que permite agregar países en entidades arbitrarias (región, nivel de
ingreso, avanzadas/no avanzadas, Latinoamérica) y comparar su diversidad de
exportación e importación a lo largo del tiempo.

Ese primitivo es real, es correcto y no está empaquetado en ningún otro lado con esa
flexibilidad de agregación. Todo lo demás en el repositorio o está roto, o está a
medio hacer, o compite en desventaja con herramientas que ya existen.

El problema no es de divulgación. Es que **la puerta de entrada está soldada**: un
desconocido no puede llegar a ver un solo número sin invertir horas. Difundir un
repositorio que no se puede correr solo convierte visitantes en gente decepcionada.

---

## 2. Qué funciona (verificado)

| Componente | Estado |
|---|---|
| `DiversityCalculator.calculate_diversity_index` | **Correcto.** Validado numéricamente |
| `TradeNetwork.from_year` + `ClassificationScheme` | **Funciona** con datos bien formados |
| Datos procesados en `data/processed_data/` | **Presentes y usables** (1995–2022, 235 países) |
| App de Streamlit | Código coherente; despliegue no verificable desde aquí |

Validación de la métrica: con 20 productos y dinero repartido uniformemente el índice
da exactamente `20.0000`; con todo el dinero concentrado en un solo producto da
exactamente `1.0000`. Es decir, el índice se lee directamente como "a cuántos
productos equivale esta canasta", que es una propiedad muy buena para comunicar y que
hoy no está documentada en ninguna parte.

---

## 3. Qué está roto (verificado por ejecución)

### 3.1 Los tres ejemplos del README fallan

Ninguno de los bloques de código del README corre. No es que estén desactualizados en
un detalle: fallan con excepción en la primera línea.

- **Quickstart**: el README llama `TradeNetwork(year=2020, ...)`.
  → `TypeError: TradeNetwork.__init__() got an unexpected keyword argument 'year'`.
  El constructor real recibe un `DataFrame`; el acceso por año es `TradeNetwork.from_year(...)`,
  añadido en un refactor posterior sin actualizar la documentación.
- **Análisis avanzado**: el README importa `EconomicComplexityAnalyzer`.
  → `ImportError`. La clase se renombró a `EconomicDiversityAnalyzer` (commit 5232508).
  Además el README la invoca como método estático, pero hoy requiere instanciación con
  `start_year`, `end_year`, `classification_schemes`, y un `base_directory` obligatorio.
- **Ruta de datos**: los ejemplos apuntan a `data/raw_data/world_bank_data/countries.csv`.
  Ese directorio **no existe en el repositorio**. Solo está `data/processed_data/`.

### 3.2 La mitad de las métricas no se puede calcular

`compute_entity_trade_metrics` —uno de los dos análisis que ofrece la librería— falla
siempre que se llega a él por el camino normal:

```
KeyError: 'mass'
```

Causa: `TradeDataLoader.load_trade_data` restringe la lectura con `usecols` a cuatro
columnas (`product_category_code`, `exporter_iso_code_3`, `importer_iso_code_3`,
`money`) y deja fuera `mass`. Pero `compute_entity_trade_metrics` calcula cuatro
métricas de masa y entropía de masa sobre esa columna ausente. `MASS_GAIN_IMPORTATION`,
`MASS_LOSS_EXPORTATION` y las dos entropías de masa son, en la práctica, código muerto.

Esto importa más de lo que parece: la masa es justamente lo que distingue este trabajo
de un análisis económico convencional — es lo que conecta con la lectura
termodinámica/ecológica que aparece en `analysis/probando_alf_ideas.ipynb`. La idea
más original del proyecto está implementada y desactivada por un `usecols`.

### 3.3 `CENTER_PERIPHERY_LEVEL` es un placeholder

En `analyzers.py` la métrica centro-periferia es `exportaciones / importaciones`, con
un comentario que admite que es "simplified" y que debería reemplazarse. Mientras
tanto, `sandbox/centro_periferia_refactor.py` contiene una implementación seria de la
metodología de Cajas (2025) —influencia comercial, retroalimentación relativa, balance
de poder— con 253 líneas bien documentadas.

**Lo mejor del repositorio está en `sandbox/` y lo peor está en el paquete publicado.**

### 3.4 No hay forma de instalarlo

No existe `pyproject.toml` ni `setup.py`. Consecuencias verificadas:

- `pip install` es imposible. El README dice "próximamente" desde hace tres años.
- El paquete solo importa si el intérprete arranca dentro del directorio del repo.
  Un script en otra carpeta falla con `ModuleNotFoundError`.
- Existe `.github/workflows/python-publish.yml`, que publica a PyPI al crear un release.
  **No puede funcionar**: ejecuta `python -m build` sobre un proyecto sin configuración
  de build. Está esperando un release que fallaría.
- Hay dos `requirements.txt` distintos y en conflicto (raíz y `complex_trade_flow/`);
  el de la raíz ni siquiera incluye `scipy`, `tqdm` ni `joblib`, que el paquete importa.

### 3.5 Configuración por variables de entorno no documentadas

`clean_trade_data.py` depende de variables que nadie puede adivinar, sin `.env.example`:

```
RAW_DATA_DIR   WBD_COUNTRIES   WBD_GDP_DEFLATOR   cleaned_data_dir
```

Nótese `cleaned_data_dir` en minúsculas mientras las demás van en mayúsculas — un
descuido que garantiza un fallo silencioso. Además se concatenan con `+` en lugar de
`Path`, así que olvidar la barra final produce un error incomprensible, y si la
variable falta el error es `TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'`.

### 3.6 Los tests no son tests

- `tests/trade_network/networks.py` y `clean_trade_data.py` no empiezan por `test_`,
  así que **pytest nunca los recoge**.
- Aunque los recogiera, usan la firma vieja `TradeNetwork(1995, [scheme])` y fallarían.
- `tests/trade_network/__init__py` tiene el punto faltante en el nombre.
- `tests/graph_db/.../test_graph_database_repository.py` importa `py2neo`, que no está
  en ningún `requirements.txt` y está descontinuado (el proyecto usa `neo4j`).
- No hay ningún workflow de CI que ejecute tests. El único workflow publica a PyPI.

Resultado: cero cobertura efectiva. El bug de `mass` sobrevivió justamente por esto.

### 3.7 Detalles de la app

En `app/main.py`, `get_palette_and_name("Latinoamerica")` devuelve un diccionario con
claves `"Latinoamérica"` / `"No Latinoamérica"`, pero la columna `is_latinoamerica` del
CSV es booleana (`True`/`False`). La intersección entre ambos conjuntos es vacía:
**la paleta de colores no se aplica nunca** y Plotly cae a colores por defecto.

---

## 4. El diagnóstico de fondo: no hay "primer número"

Esta es la razón por la que el repositorio tiene 2 estrellas y ningún usuario.

Para que un desconocido vea **un solo resultado**, hoy tiene que:

1. Clonar (no puede instalar).
2. Registrarse en CEPII y descargar BACI HS92 — varios GB, detrás de un formulario.
3. Descargar por separado indicadores del Banco Mundial.
4. Adivinar cuatro variables de entorno no documentadas.
5. Correr un bucle de limpieza sobre 28 años, secuencial, sin paralelizar (hay un TODO
   admitiéndolo).
6. Descubrir que los ejemplos del README no corren y leer el código fuente para
   reconstruir la API real.

El tiempo hasta el primer número es, para efectos prácticos, infinito. Y hay una
ironía cruel: **el repositorio ya contiene los resultados procesados** en
`data/processed_data/` — 1995 a 2022, 235 países, listos para usar. El valor ya está
ahí, pero está enterrado bajo una cadena de instalación que nadie va a completar.

---

## 5. Qué rescatar y qué cortar

### Rescatar (el núcleo, ~200 líneas reales)

- `DiversityCalculator` — correcto y validado. Es el activo principal.
- `ClassificationScheme` — la idea de agregar países en entidades arbitrarias es la
  diferenciación real frente a `py-ecomplexity` o el paquete `economiccomplexity` de R,
  que dan ECI/PCI/RCA pero no esta flexibilidad de agregación.
- `TradeNetwork` (vía `from_year`) — funciona, solo necesita cargar `mass`.
- Los CSV de `data/processed_data/` — resultados reales de 28 años. Subvalorados.
- `sandbox/centro_periferia_refactor.py` — **promover al paquete con tests.** Es la
  contribución más original y no está disponible en ninguna otra librería.

### Cortar o archivar

- **`graph_db/`** — el método que importaría los datos de comercio (`upload_trade_data`)
  es literalmente `pass`. Arrastra Neo4j y `py2neo` como dependencias y no entrega nada.
  Un grafo de comercio no aporta sobre un DataFrame para estas métricas.
- **`sandbox/`** — mover `centro_periferia_refactor.py` al paquete y archivar el resto
  en una rama. Hoy 1.470 líneas de código muerto compiten visualmente con el paquete real.
- **`.github/workflows/python-publish.yml`** — o se acompaña de `pyproject.toml`, o se
  borra. Hoy es una trampa.
- **`requirements.txt` duplicado** — consolidar en `pyproject.toml`.

### Reposicionar

El README promete "Análisis de Complejidad Económica". El repositorio **no implementa
complejidad económica** (no hay ECI, PCI, RCA ni espacio de producto). Implementa
*diversidad*, que es otra cosa. Quien llegue buscando complejidad económica se va a ir;
quien buscaba diversidad no encuentra el repositorio porque no se llama así.

Nota de discoverability: GitHub clasifica el repositorio como **"Jupyter Notebook"**
porque los notebooks dominan el tamaño. Aparece como una colección de notebooks, no
como una librería de Python.

---

## 6. Camino recomendado

Ordenado por relación impacto/esfuerzo. Los tres primeros son los que mueven la aguja.

**1. `pyproject.toml` y `pip install -e .`** (1 hora)
Desbloquea todo lo demás: importar desde cualquier parte, CI, PyPI, y que el workflow
existente deje de ser ficción.

**2. Un dataset de ejemplo incluido en el repo** (medio día) — *la más importante*
Un solo año, un subconjunto de países y productos, unos pocos MB versionables. Meta
concreta:

```bash
pip install complex-trade-flow
python -m complex_trade_flow.demo
```

y que en menos de 30 segundos, sin descargar nada ni registrarse en ninguna parte,
salga un número y una gráfica. Esto convierte el proyecto de "no ejecutable" a
"ejecutable", que es el único salto que realmente importa. Todo lo demás es pulido.

**3. Arreglar lo verificado como roto** (medio día)
Añadir `mass` al `usecols`; reescribir los ejemplos del README **copiándolos de un test
que corra en CI** (así no se vuelven a desincronizar); renombrar los tests a `test_*.py`
y actualizarlos a la API actual; añadir un workflow de CI que ejecute pytest.

**4. Documentar la métrica** (2 horas)
Explicar que el índice es `2^H`, el número de Hill de orden 1, y que se lee como
"número efectivo de productos". Citar la literatura de diversidad (Hill 1973, Jost 2006)
y decir explícitamente en qué se diferencia de ECI/PCI. Esto es lo que da credibilidad
científica y hoy no está escrito en ningún lado.

**5. Promover centro-periferia** (1–2 días)
Sacarlo de `sandbox/`, meterlo en el paquete con tests, y reemplazar el placeholder de
`CENTER_PERIPHERY_LEVEL`. Es lo que hace este proyecto único.

**6. Recién entonces, divulgar**
Con lo anterior hecho hay algo que contar: no "hice una librería", sino un hallazgo
—la diversidad de exportaciones cae a lo largo del tiempo y se comporta distinto en
el norte y el sur— respaldado por código que cualquiera puede correr en 30 segundos.
El hallazgo es el gancho; la librería es la evidencia.

---

## 7. Una decisión que conviene tomar explícitamente

Hoy hay **dos productos enredados** en un solo repositorio:

- **(A) Un artefacto de investigación**: la evidencia de que la diversidad comercial
  cae, con la app de Streamlit, los notebooks y los CSV procesados. Está casi terminado
  y tiene audiencia — la issue #12 es una persona real pidiendo análisis concretos.
- **(B) Una librería de Python de propósito general** para que terceros calculen estas
  métricas. Está lejos y compite con herramientas establecidas.

El repositorio se presenta como (B), que es la venta más difícil y la oferta más débil.
La recomendación es liderar con (A) y dejar que (B) sea el respaldo de
reproducibilidad. Un hallazgo con código que lo respalda se difunde solo; una librería
genérica sin usuarios necesita marketing que nadie va a hacer.

Sobre el idioma: el README está en español y el código mezcla ambos. Contra la
intuición, **el español es un activo aquí**, no un problema: prácticamente no existe
herramienta de complejidad y diversidad económica documentada en español, y la
audiencia natural de un análisis centrado en Latinoamérica es hispanohablante. La
recomendación es README bilingüe con español primero, y unificar el código en inglés
(nombres e identificadores) manteniendo docstrings en español.

---

## 8. Si solo se hiciera una cosa

Incluir un dataset de ejemplo y hacer que `pip install` funcione.

El resto de los problemas de este documento son molestias. Ese es el único que impide
estructuralmente que exista un usuario.
