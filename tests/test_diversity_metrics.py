"""
Tests de la métrica de diversidad.

El índice es 2^H (número de Hill de orden 1), que se interpreta como "número
efectivo de productos". Esa interpretación tiene consecuencias verificables y
son las que se comprueban acá.
"""

import numpy as np
import pandas as pd
import pytest

from complex_trade_flow import DiversityCalculator


def build_data(values: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {"product_category_code": range(len(values)), "money": values}
    )


def test_distribucion_uniforme_da_el_numero_de_productos():
    """Con N productos de igual valor, la diversidad efectiva debe ser N."""
    for n in (2, 5, 20, 100):
        assert DiversityCalculator.calculate_diversity_index(
            build_data([100.0] * n)
        ) == pytest.approx(n)


def test_concentracion_total_da_uno():
    """Si todo el valor está en un producto, la canasta equivale a 1 producto."""
    data = build_data([1000.0] + [0.0] * 19)
    assert DiversityCalculator.calculate_diversity_index(data) == pytest.approx(1.0)


def test_la_diversidad_nunca_supera_el_conteo_de_productos():
    rng = np.random.default_rng(0)
    for _ in range(20):
        values = rng.random(30) * 1000
        index = DiversityCalculator.calculate_diversity_index(build_data(list(values)))
        assert 1.0 <= index <= 30.0 + 1e-9


def test_concentrar_valor_reduce_la_diversidad():
    """Mover valor hacia un solo producto tiene que bajar el índice."""
    plana = DiversityCalculator.calculate_diversity_index(build_data([10.0] * 10))
    sesgada = DiversityCalculator.calculate_diversity_index(
        build_data([100.0] + [10.0] * 9)
    )
    concentrada = DiversityCalculator.calculate_diversity_index(
        build_data([10_000.0] + [10.0] * 9)
    )
    assert plana > sesgada > concentrada


def test_es_invariante_a_la_escala():
    """Multiplicar todos los valores por una constante no cambia la diversidad."""
    base = build_data([5.0, 10.0, 85.0])
    escalada = build_data([500.0, 1000.0, 8500.0])
    assert DiversityCalculator.calculate_diversity_index(
        base
    ) == pytest.approx(DiversityCalculator.calculate_diversity_index(escalada))


def test_probabilidades_marginales_suman_uno():
    probabilities = DiversityCalculator.calculate_marginal_probabilities(
        category="product_category_code",
        data=build_data([3.0, 7.0, 15.0]),
        column="money",
    )
    assert probabilities.sum() == pytest.approx(1.0)


def test_se_puede_calcular_sobre_masa_y_no_solo_dinero():
    data = pd.DataFrame(
        {
            "product_category_code": [1, 2, 3, 4],
            "money": [100.0, 100.0, 100.0, 100.0],
            "mass": [1000.0, 0.0, 0.0, 0.0],
        }
    )
    por_dinero = DiversityCalculator.calculate_diversity_index(data, column="money")
    por_masa = DiversityCalculator.calculate_diversity_index(data, column="mass")
    assert por_dinero == pytest.approx(4.0)
    assert por_masa == pytest.approx(1.0)
