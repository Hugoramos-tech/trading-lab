"""Fase 0: establecer el rival a batir.

Ejecuta comprar-y-mantener sobre el S&P 500 con costes realistas y lo registra
en el diario de experimentos. Todo lo que se construya despues se compara
contra este numero.

    python scripts/run_benchmark.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from lab import backtest, metrics
from lab.costs import ALPACA_ZERO_COMMISSION, IBKR_FIXED_EUROPE, FREE_FANTASY
from lab.data import load_prices
from lab.journal import Journal


def main() -> None:
    print(f"Descargando {config.BENCHMARK_TICKER}...")
    prices = load_prices(config.BENCHMARK_TICKER, start="2015-01-01")
    print(f"  {len(prices)} dias, de {prices.index.min().date()} "
          f"a {prices.index.max().date()}\n")

    jr = Journal()
    exp_id = jr.declare(
        hypothesis="Referencia: comprar y mantener el indice. Sin hipotesis "
                   "de ineficiencia; es el rival a batir.",
        params={"ticker": config.BENCHMARK_TICKER, "start": "2015-01-01"},
    )

    escenarios = {
        "Sin costes (fantasia)": FREE_FANTASY,
        "Alpaca (0 % comision)": ALPACA_ZERO_COMMISSION,
        "IBKR Europa (min 3 EUR)": IBKR_FIXED_EUROPE,
    }

    resultados = {}
    for nombre, modelo in escenarios.items():
        res = backtest.buy_and_hold(prices, modelo)
        resultados[nombre] = res.stats
        print(f"--- {nombre} ---")
        print(res.report())

    jr.record(exp_id, resultados, notes="Benchmark de referencia de la fase 0")

    n = jr.n_trials()
    print("=" * 52)
    print(f"Experimentos declarados hasta ahora (N): {n}")
    print(f"Sharpe maximo esperado por azar con N={n}: "
          f"{metrics.expected_max_sharpe(max(n, 2)):.3f}")
    print(f"Anos de datos necesarios si llegas a 1.000 pruebas: "
          f"{metrics.min_backtest_length(1000):.1f}")
    print("=" * 52)


if __name__ == "__main__":
    main()
