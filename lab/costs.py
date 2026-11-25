"""Modelo de costes de ejecucion.

CONCEPTO CLAVE
--------------
La reproduccion de los agentes LLM publicados mostro que el Sharpe de
TradingAgents cayo de 0,43 a 0,22 solo por incluir costes. En microcaps, un
coste del 3 % hace que una senal con 5,2 % de retorno medio pierda la
significancia estadistica por completo.

Conclusion de ingenieria: los costes no son un detalle que se ajusta al final.
Son el filtro principal. Una estrategia se disena para minimizar operaciones,
no para maximizar aciertos.

Los tres componentes:
  - Comision: lo que cobra el broker. Porcentual, con posible minimo por orden.
  - Horquilla (spread): compras al precio de oferta, vendes al de demanda.
    Pierdes media horquilla en cada lado. Es el coste invisible.
  - Deslizamiento (slippage): el precio se mueve entre que decides y ejecutas.
"""
from __future__ import annotations

from dataclasses import dataclass

import config

BPS = 1e-4  # un punto basico = 0,01 %


@dataclass(frozen=True)
class CostModel:
    """Coste de una operacion. Inmutable: un backtest no puede cambiarlo a mitad."""

    commission_pct: float = config.DEFAULT_COMMISSION_PCT
    commission_min: float = config.DEFAULT_COMMISSION_MIN
    spread_bps: float = config.DEFAULT_SPREAD_BPS
    slippage_bps: float = config.DEFAULT_SLIPPAGE_BPS

    def commission(self, notional: float) -> float:
        """Comision de una orden por importe `notional`."""
        return max(abs(notional) * self.commission_pct, self.commission_min)

    def market_impact(self, notional: float) -> float:
        """Coste de horquilla + deslizamiento.

        Se paga media horquilla por lado, mas el deslizamiento completo.
        """
        rate = (self.spread_bps / 2 + self.slippage_bps) * BPS
        return abs(notional) * rate

    def total(self, notional: float) -> float:
        """Coste total de mover `notional` en una sola orden."""
        if notional == 0:
            return 0.0
        return self.commission(notional) + self.market_impact(notional)

    def round_trip(self, notional: float) -> float:
        """Coste de entrar y salir: lo que la estrategia debe batir para empatar."""
        return 2 * self.total(notional)

    def breakeven_pct(self, notional: float) -> float:
        """Rentabilidad minima (en tanto por uno) para no perder dinero.

        Este numero es la prueba de realidad de cualquier estrategia:
        si su ganancia media por operacion no supera esto, pierde.
        """
        return self.round_trip(notional) / abs(notional)


# Perfiles predefinidos de brokers reales, para comparar escenarios.
ALPACA_ZERO_COMMISSION = CostModel(
    commission_pct=0.0, commission_min=0.0, spread_bps=10.0, slippage_bps=5.0
)
"""Alpaca: sin comision en acciones de EEUU. Solo horquilla y deslizamiento."""

IBKR_FIXED_EUROPE = CostModel(
    commission_pct=0.0005, commission_min=3.0, spread_bps=15.0, slippage_bps=5.0
)
"""IBKR tarifa fija Europa: 0,05 % con minimo de 3 EUR. El minimo es el que mata
cuentas pequenas: con 25 EUR de posicion, la ida y vuelta cuesta un 24 %."""

FREE_FANTASY = CostModel(0.0, 0.0, 0.0, 0.0)
"""Sin costes. NO usar para evaluar: existe solo para medir cuanto se come la
friccion comparando contra un modelo realista."""
