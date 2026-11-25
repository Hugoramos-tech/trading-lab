"""Configuracion central del laboratorio.

Todo parametro que afecte a un resultado vive aqui, no disperso en el codigo:
si un backtest no es reproducible, no es un backtest.
"""
from pathlib import Path

BASE_DIR = Path(__file__).parent
CACHE_DIR = BASE_DIR / "cache"
JOURNAL_DB = BASE_DIR / "journal.db"

# --- Mercado de referencia -------------------------------------------------
BENCHMARK_TICKER = "SPY"   # el rival a batir: comprar y mantener el S&P 500
TRADING_DAYS_YEAR = 252    # dias de mercado al ano (convencion estandar)

# --- Costes de ejecucion ---------------------------------------------------
# Valores por defecto deliberadamente PESIMISTAS. Es mejor que una estrategia
# muera aqui que con dinero real.
DEFAULT_COMMISSION_PCT = 0.0005   # 0,05 % del importe
DEFAULT_COMMISSION_MIN = 0.0      # minimo por orden en EUR/USD (Alpaca: 0)
DEFAULT_SPREAD_BPS = 10.0         # 10 puntos basicos = 0,10 % de horquilla
DEFAULT_SLIPPAGE_BPS = 5.0        # 5 pb de deslizamiento al ejecutar

# --- Capital simulado ------------------------------------------------------
INITIAL_CAPITAL = 10_000.0
