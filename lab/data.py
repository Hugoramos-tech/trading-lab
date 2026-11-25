"""Ingesta de precios con cache local y guardia anti-look-ahead.

CONCEPTO CLAVE (look-ahead bias)
--------------------------------
El error que arruina la mayoria de los backtests es usar, al decidir en la
fecha T, informacion que solo estuvo disponible despues de T. Ocurre de formas
sutiles: un indicador calculado sobre toda la serie, un precio de cierre usado
para decidir una compra "al cierre" de ese mismo dia, un dato corregido a
posteriori...

La defensa no es tener cuidado: es que el codigo NO PUEDA ver el futuro.
De eso se encarga PriceView.
"""
from __future__ import annotations

import pandas as pd

import config


class LookAheadError(RuntimeError):
    """Se intento leer informacion posterior a la fecha de decision."""


def load_prices(ticker: str, start: str = "2015-01-01", end: str | None = None,
                force_refresh: bool = False) -> pd.DataFrame:
    """Descarga OHLCV diario y lo cachea en parquet.

    La cache evita descargar lo mismo mil veces y, sobre todo, congela los
    datos: dos ejecuciones del mismo backtest usan exactamente la misma serie.
    """
    config.CACHE_DIR.mkdir(exist_ok=True)
    path = config.CACHE_DIR / f"{ticker.upper()}_{start}_{end or 'latest'}.parquet"

    if path.exists() and not force_refresh:
        return pd.read_parquet(path)

    import yfinance as yf
    df = yf.download(ticker, start=start, end=end, auto_adjust=True,
                     progress=False)
    if df.empty:
        raise ValueError(f"Sin datos para {ticker}")

    # yfinance devuelve columnas MultiIndex cuando se pide un solo ticker en
    # versiones recientes; las aplanamos para trabajar comodos.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower().replace(" ", "_") for c in df.columns]
    df.index.name = "date"

    df.to_parquet(path)
    return df


class PriceView:
    """Vista de una serie de precios limitada a una fecha de decision.

    Un objeto PriceView solo deja leer datos ESTRICTAMENTE anteriores o iguales
    a `as_of`. Cualquier intento de leer mas alla lanza LookAheadError.

    Uso tipico dentro de una estrategia:

        view = PriceView(df, as_of="2020-03-10")
        historia = view.history()        # todo hasta 2020-03-10 incluido
        ultimo = view.last_close()       # cierre del 2020-03-10

    Lo que NO se puede hacer:

        view.df.loc["2020-03-11"]        # AttributeError: no existe .df
    """

    __slots__ = ("_data", "_as_of")

    def __init__(self, data: pd.DataFrame, as_of: str | pd.Timestamp):
        self._as_of = pd.Timestamp(as_of)
        # El recorte se hace UNA vez, en el constructor. Lo que queda fuera
        # simplemente no esta en el objeto: no hay forma de llegar a el.
        self._data = data.loc[:self._as_of].copy()
        if self._data.empty:
            raise ValueError(f"No hay datos anteriores a {self._as_of.date()}")

    @property
    def as_of(self) -> pd.Timestamp:
        return self._as_of

    def history(self, lookback: int | None = None) -> pd.DataFrame:
        """Historia visible. `lookback` limita a los N ultimos dias."""
        return self._data if lookback is None else self._data.tail(lookback)

    def last_close(self) -> float:
        return float(self._data["close"].iloc[-1])

    def at(self, date: str | pd.Timestamp) -> pd.Series:
        """Fila de una fecha concreta, si es visible."""
        ts = pd.Timestamp(date)
        if ts > self._as_of:
            raise LookAheadError(
                f"Intento de leer {ts.date()} desde una vista fijada en "
                f"{self._as_of.date()}. Eso es mirar el futuro."
            )
        return self._data.loc[ts]

    def __repr__(self) -> str:
        return (f"PriceView(as_of={self._as_of.date()}, "
                f"visible={len(self._data)} dias)")


def walk_forward_dates(data: pd.DataFrame, start: str,
                       step: int = 1) -> list[pd.Timestamp]:
    """Genera las fechas de decision para recorrer la historia hacia delante.

    Recorrer con estas fechas y construir un PriceView en cada una es la forma
    honesta de simular: en cada paso solo existe el pasado.
    """
    idx = data.loc[pd.Timestamp(start):].index
    return list(idx[::step])
