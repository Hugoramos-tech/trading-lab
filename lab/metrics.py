"""Metricas de rendimiento y de honestidad estadistica.

Las primeras (Sharpe, drawdown, CAGR) dicen como fue. La ultima, el Deflated
Sharpe Ratio, dice si deberiamos creerlo.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

import config

EULER_MASCHERONI = 0.5772156649015329


def total_return(equity: pd.Series) -> float:
    return float(equity.iloc[-1] / equity.iloc[0] - 1)


def cagr(equity: pd.Series) -> float:
    """Rentabilidad anualizada compuesta."""
    years = len(equity) / config.TRADING_DAYS_YEAR
    if years <= 0:
        return 0.0
    return float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1)


def sharpe(returns: pd.Series, risk_free: float = 0.0) -> float:
    """Sharpe anualizado. Retorno por unidad de volatilidad.

    Referencia: comprar y mantener el S&P 500 ronda 0,5-0,7 historicamente.
    Un Sharpe de 2 en un backtest casero es, casi siempre, un error o
    sobreajuste, no un hallazgo.
    """
    excess = returns - risk_free / config.TRADING_DAYS_YEAR
    sd = excess.std()
    if sd == 0 or np.isnan(sd):
        return 0.0
    return float(excess.mean() / sd * np.sqrt(config.TRADING_DAYS_YEAR))


def max_drawdown(equity: pd.Series) -> float:
    """Maxima caida desde un maximo previo. Lo que de verdad duele."""
    return float((equity / equity.cummax() - 1).min())


def summary(equity: pd.Series) -> dict[str, float]:
    returns = equity.pct_change().dropna()
    return {
        "total_return": total_return(equity),
        "cagr": cagr(equity),
        "sharpe": sharpe(returns),
        "max_drawdown": max_drawdown(equity),
        "volatility": float(returns.std() * np.sqrt(config.TRADING_DAYS_YEAR)),
        "days": len(equity),
    }


def expected_max_sharpe(n_trials: int, sharpe_variance: float = 1.0) -> float:
    """Sharpe maximo esperado al probar `n_trials` estrategias SIN NINGUNA SKILL.

    Si pruebas 1.000 variantes de una estrategia aleatoria, la mejor tendra un
    Sharpe alto por puro azar. Este es ese umbral: lo que hay que superar para
    que el resultado signifique algo.
    """
    if n_trials < 2:
        return 0.0
    sd = np.sqrt(sharpe_variance)
    z1 = stats.norm.ppf(1 - 1 / n_trials)
    z2 = stats.norm.ppf(1 - 1 / (n_trials * np.e))
    return float(sd * ((1 - EULER_MASCHERONI) * z1 + EULER_MASCHERONI * z2))


def deflated_sharpe_ratio(observed_sharpe: float, n_trials: int, n_obs: int,
                          skew: float = 0.0, kurtosis: float = 3.0,
                          sharpe_variance: float = 1.0) -> float:
    """Deflated Sharpe Ratio (Bailey y Lopez de Prado).

    Devuelve la PROBABILIDAD de que el Sharpe observado sea real y no fruto de
    haber probado muchas configuraciones y quedarse con la mejor.

    Interpretacion: < 0,95 significa que no se puede descartar el azar.

    NOTA: implementacion segun la formulacion estandar del paper. Antes de
    tomar decisiones con dinero, verificar contra el original:
    https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551
    """
    sr0 = expected_max_sharpe(n_trials, sharpe_variance)
    # Desviacion tipica del estimador de Sharpe, corregida por asimetria y
    # curtosis: los retornos financieros no son normales.
    denom = 1 - skew * observed_sharpe + (kurtosis - 1) / 4 * observed_sharpe**2
    if denom <= 0 or n_obs < 2:
        return float("nan")
    z = (observed_sharpe - sr0) * np.sqrt(n_obs - 1) / np.sqrt(denom)
    return float(stats.norm.cdf(z))


def min_backtest_length(n_trials: int, target_sharpe: float = 1.0) -> float:
    """Anos minimos de datos necesarios para `n_trials` pruebas (MinBTL).

    MinBTL ~= 2 * ln(N) / E[max_Sharpe]^2

    Ejemplo: 1.000 configuraciones probadas buscando un Sharpe de 1,0
    requieren ~13,8 anos de datos. Cada barrido de parametros consume
    credibilidad: por eso las hipotesis se declaran ANTES de ejecutarlas.
    """
    if n_trials < 2 or target_sharpe <= 0:
        return 0.0
    return float(2 * np.log(n_trials) / target_sharpe**2)
