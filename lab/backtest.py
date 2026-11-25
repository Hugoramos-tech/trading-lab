"""Motor de backtest vectorizado, deliberadamente simple.

Son pocas lineas a proposito: tienes que poder leerlo entero y entender
exactamente que esta simulando. Un motor que no entiendes es un motor en el que
no puedes detectar un sesgo a tu favor.

REGLA DE ORO
------------
Las senales se generan con datos del dia T y se ejecutan al precio de APERTURA
del dia T+1. Nunca al cierre de T: ese precio no lo conocias cuando decidiste.
Esa linea (`.shift(1)`) es la diferencia entre un backtest y una fantasia.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

import config
from lab import metrics
from lab.costs import CostModel


@dataclass
class BacktestResult:
    equity: pd.Series
    positions: pd.Series
    costs_paid: pd.Series
    stats: dict = field(default_factory=dict)

    @property
    def n_trades(self) -> int:
        """Numero de cambios de posicion. Cada uno cuesta dinero."""
        return int((self.positions.diff().fillna(0) != 0).sum())

    def report(self) -> str:
        s = self.stats
        return (
            f"  Retorno total : {s['total_return']:>8.2%}\n"
            f"  CAGR          : {s['cagr']:>8.2%}\n"
            f"  Sharpe        : {s['sharpe']:>8.2f}\n"
            f"  Max drawdown  : {s['max_drawdown']:>8.2%}\n"
            f"  Volatilidad   : {s['volatility']:>8.2%}\n"
            f"  Operaciones   : {self.n_trades:>8d}\n"
            f"  Costes totales: {self.costs_paid.sum():>8.2f}\n"
        )


def run(prices: pd.DataFrame, signal: pd.Series, cost_model: CostModel,
        initial_capital: float = config.INITIAL_CAPITAL) -> BacktestResult:
    """Simula una estrategia.

    Parametros
    ----------
    prices : DataFrame con columnas 'open' y 'close', indexado por fecha.
    signal : Serie con la posicion OBJETIVO para cada dia (0 = fuera,
             1 = totalmente invertido). Se asume calculada con datos de ese dia.
    cost_model : modelo de costes a aplicar.
    """
    px = prices.copy()
    # El desplazamiento critico: la senal de hoy se ejecuta manana.
    position = signal.reindex(px.index).ffill().fillna(0).shift(1).fillna(0)

    # Retorno del activo de apertura a apertura (coherente con ejecutar en la
    # apertura del dia siguiente).
    asset_returns = px["open"].pct_change().fillna(0)

    equity = pd.Series(index=px.index, dtype=float)
    costs_paid = pd.Series(0.0, index=px.index)
    capital = initial_capital
    prev_pos = 0.0

    for date in px.index:
        pos = float(position.loc[date])
        # 1. El capital se mueve con el mercado segun la posicion de ayer.
        capital *= 1 + prev_pos * float(asset_returns.loc[date])
        # 2. Si la posicion cambia, se paga el coste de ese cambio.
        if pos != prev_pos:
            notional = abs(pos - prev_pos) * capital
            cost = cost_model.total(notional)
            capital -= cost
            costs_paid.loc[date] = cost
        equity.loc[date] = capital
        prev_pos = pos

    return BacktestResult(
        equity=equity,
        positions=position,
        costs_paid=costs_paid,
        stats=metrics.summary(equity),
    )


def buy_and_hold(prices: pd.DataFrame, cost_model: CostModel,
                 initial_capital: float = config.INITIAL_CAPITAL) -> BacktestResult:
    """El rival a batir: comprar el primer dia y no tocar nada mas.

    Toda estrategia que no supere esto, despues de costes, es trabajo perdido.
    """
    signal = pd.Series(1.0, index=prices.index)
    return run(prices, signal, cost_model, initial_capital)
