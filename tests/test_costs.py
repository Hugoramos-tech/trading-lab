"""Los costes son el filtro principal: conviene que esten bien medidos."""
from lab.costs import IBKR_FIXED_EUROPE, ALPACA_ZERO_COMMISSION, CostModel


def test_minimo_de_comision_arruina_cuentas_pequenas():
    """Con 25 EUR en IBKR, la ida y vuelta se come casi un cuarto del capital."""
    breakeven = IBKR_FIXED_EUROPE.breakeven_pct(25.0)
    assert breakeven > 0.20, f"esperado >20%, obtenido {breakeven:.1%}"


def test_el_minimo_deja_de_pesar_con_capital_mayor():
    assert IBKR_FIXED_EUROPE.breakeven_pct(5000.0) < 0.01


def test_alpaca_sin_comision_solo_paga_friccion():
    """Sin comision quedan horquilla y deslizamiento: ~0,20 % ida y vuelta."""
    be = ALPACA_ZERO_COMMISSION.breakeven_pct(1000.0)
    assert 0.001 < be < 0.005


def test_coste_cero_cuando_no_se_opera():
    assert CostModel().total(0) == 0.0
