"""
Ejecuta los ejemplos de código del README.

Este test existe porque los tres ejemplos del README estuvieron rotos durante
meses: la firma de `TradeNetwork` cambió, `EconomicComplexityAnalyzer` se
renombró, y las rutas de datos que citaban no existían en el repositorio. Nada
lo detectó porque la documentación no se ejecutaba nunca.

Un bloque ```python del README se ejecuta salvo que su primera línea sea el
comentario `# requiere-datos-reales`, reservado para ejemplos que dependen de
descargar BACI.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

README = Path(__file__).resolve().parents[1] / "README.md"
SKIP_MARKER = "# requiere-datos-reales"

BLOCK_PATTERN = re.compile(r"^```python\n(.*?)^```", re.MULTILINE | re.DOTALL)


def readme_python_blocks() -> list[tuple[int, str]]:
    if not README.exists():  # pragma: no cover
        return []
    text = README.read_text(encoding="utf-8")
    blocks = []
    for match in BLOCK_PATTERN.finditer(text):
        line_number = text[: match.start()].count("\n") + 1
        blocks.append((line_number, match.group(1)))
    return blocks


BLOCKS = readme_python_blocks()


def test_el_readme_tiene_ejemplos():
    assert BLOCKS, "No se encontró ningún bloque ```python en el README"


@pytest.mark.parametrize(
    "line_number,source",
    BLOCKS,
    ids=[f"README-linea-{line}" for line, _ in BLOCKS],
)
def test_el_ejemplo_del_readme_corre(line_number: int, source: str):
    if source.lstrip().startswith(SKIP_MARKER):
        pytest.skip("ejemplo que requiere datos reales de BACI")

    namespace: dict = {"__name__": "__readme__"}
    try:
        exec(compile(source, f"README.md:{line_number}", "exec"), namespace)
    except Exception as error:  # pragma: no cover - el mensaje es el valor
        pytest.fail(
            f"El ejemplo del README en la línea {line_number} falló con "
            f"{type(error).__name__}: {error}\n\n{source}"
        )
