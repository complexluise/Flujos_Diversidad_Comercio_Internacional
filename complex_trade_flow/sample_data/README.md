# Datos de ejemplo — SINTÉTICOS

> **Estos archivos NO son datos de comercio reales.**
>
> No los uses para sacar conclusiones sustantivas sobre comercio internacional,
> ni cites ningún número derivado de ellos. Existen únicamente para que la
> librería se pueda instalar, ejecutar y testear sin descargar varios GB de datos
> detrás de un registro.

## Qué contienen

| Archivo | Contenido |
|---|---|
| `cleaned_HS92_Y2020_SAMPLE.csv` | ~32.000 flujos sintéticos entre 42 países y 126 productos, con la misma forma que BACI-CEPII ya limpio |
| `countries_SAMPLE.csv` | Los 42 países con su región del Banco Mundial, en el formato que espera `ClassificationScheme` |

Los códigos de país (ISO-3) y los capítulos HS92 son reales; los flujos de dinero
y masa son generados.

## Cómo se generaron

Con `scripts/generate_sample_data.py`, que es determinista (semilla fija) y está
versionado justamente para que el proceso sea auditable: cualquiera puede leer el
modelo generativo y regenerar los archivos byte a byte.

```bash
python scripts/generate_sample_data.py
```

El modelo incorpora tres hechos estilizados del comercio real, para que los
resultados del demo sean pedagógicamente correctos aunque los datos sean falsos:

1. **Gravedad** — los países grandes y cercanos comercian más entre sí.
2. **Capacidades** — las economías grandes exportan canastas más variadas.
3. **Ley de potencias** — dentro de la canasta de cada país unos pocos productos
   concentran la mayor parte del valor, que es exactamente la razón por la cual
   la *diversidad efectiva* que mide esta librería es bastante menor que el
   conteo crudo de productos.

Con estos datos, el orden de diversidad de exportaciones que resulta es el
esperado (Estados Unidos, China y Alemania arriba; Argentina, Chile y Ecuador
abajo), pero las magnitudes son artefactos del generador.

## Para trabajar con datos reales

Los datos reales hay que descargarlos por separado:

- **BACI** (CEPII): http://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37
- **Indicadores del Banco Mundial**: https://data.worldbank.org/

Ver la sección "Datos reales" del README principal.
