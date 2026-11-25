"""El test mas importante del laboratorio.

Si estos tests pasan, el codigo no puede mirar el futuro. Si alguna vez fallan,
cualquier resultado obtenido desde entonces es sospechoso.
"""
import pandas as pd
import pytest

from lab.data import LookAheadError, PriceView


@pytest.fixture
def sample():
    idx = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame(
        {"open": range(10), "close": range(10, 20), "volume": [1000] * 10},
        index=idx,
    )


def test_view_solo_ve_el_pasado(sample):
    view = PriceView(sample, as_of="2024-01-05")
    assert len(view.history()) == 5
    assert view.history().index.max() == pd.Timestamp("2024-01-05")


def test_leer_el_futuro_lanza_error(sample):
    view = PriceView(sample, as_of="2024-01-05")
    with pytest.raises(LookAheadError):
        view.at("2024-01-06")


def test_no_hay_acceso_al_dataframe_completo(sample):
    """PriceView usa __slots__: no se le pueden anadir atributos ni hay .df."""
    view = PriceView(sample, as_of="2024-01-05")
    assert not hasattr(view, "df")
    with pytest.raises(AttributeError):
        view.datos_completos = sample


def test_lookback_limita_la_historia(sample):
    view = PriceView(sample, as_of="2024-01-08")
    assert len(view.history(lookback=3)) == 3


def test_vista_sin_datos_falla(sample):
    with pytest.raises(ValueError):
        PriceView(sample, as_of="2023-01-01")


def test_senal_se_ejecuta_al_dia_siguiente():
    """Verifica el .shift(1) del motor: una senal no puede operar el mismo dia."""
    from lab.backtest import run
    from lab.costs import FREE_FANTASY

    idx = pd.date_range("2024-01-01", periods=5, freq="D")
    prices = pd.DataFrame({"open": [100, 100, 200, 200, 200],
                           "close": [100, 100, 200, 200, 200]}, index=idx)
    # Senal que "adivina" el salto justo el dia que ocurre.
    signal = pd.Series([0, 1, 0, 0, 0], index=idx, dtype=float)
    result = run(prices, signal, FREE_FANTASY, initial_capital=1000.0)
    # La senal del dia 2 se ejecuta el dia 3, capturando el salto de 100 a 200.
    # Si el motor ejecutara el mismo dia, el resultado seria distinto.
    assert result.positions.iloc[1] == 0.0, "la senal no puede operar el dia 1"
    assert result.positions.iloc[2] == 1.0, "debe estar dentro el dia 3"
