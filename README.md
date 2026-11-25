# trading-lab

> Laboratorio para diseñar, medir y **descartar** estrategias de trading algorítmico,
> con una capa de IA para analizar texto financiero. Construido sobre la premisa de que
> la parte difícil no es escribir el algoritmo, sino averiguar si funciona de verdad.

[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-10%20passing-brightgreen.svg)](#ejecutar)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Por qué existe este proyecto

La mayoría de los proyectos de "bot de trading con IA" fracasan por la misma razón: están
diseñados para **desplegar** una estrategia, no para **falsarla**. Producen un backtest
precioso, se despliegan, y pierden dinero.

Este laboratorio invierte la prioridad. Está construido para que una estrategia mala muera
en el banco de pruebas y no con dinero real. Las dos primeras piezas que se escribieron no
generan señales: una impide mirar el futuro y la otra cobra los costes de ejecución.

### La evidencia que condiciona el diseño

Antes de escribir una línea de código se revisó qué dice la literatura de 2026 sobre
agentes LLM que operan en bolsa. El resultado es consistente y poco halagüeño:

| Hallazgo | Dato |
|---|---|
| El alfa desaparece al incluir costes | Reproducción de TradingAgents: Sharpe **0,43 → 0,22** |
| Contaminación temporal | FinMem pierde **~72 %** del retorno cuando el periodo de test cruza su fecha de corte de entrenamiento |
| Frente a comprar y mantener | Buy & hold: Sharpe **0,703**. FinAgent: 0,241. FinMem: **−0,228** |
| Alfa real | En un benchmark sin look-ahead, **ningún** run mostró alfa significativa de 4 factores: ganan *beta*, no habilidad |
| Prácticas de reporte | De 40 celdas sistema × fricción revisadas, **35 no modelaban fricción alguna** |

Y sobre las anomalías publicadas:

- McLean & Pontiff (97 predictores): los retornos caen **~26 % fuera de muestra** y
  **~58 % más tras publicarse**.
- Jacobs & Müller (241 anomalías, 39 mercados): caída post-publicación del **62-66 %** en EEUU.
- Estimaciones de sesgo de publicación: **~la mitad** del decaimiento corresponde a
  anomalías que nunca existieron del todo.

**Conclusión de ingeniería:** toda estrategia documentada en un libro o un blog está
muerta o moribunda. Cruces de medias móviles y RSI no son puntos de partida, son ruido
arbitrado hace décadas. Lo que sobrevive, sobrevive por una **razón estructural**.

### Dónde queda ventaja real

Un estudio sobre señales de insiders en microcaps mide el límite al arbitraje:

> Una orden de **50.000 $ supera el 5 % del volumen diario** en el **53,3 %** de los
> eventos de la muestra.

Un fondo grande no puede entrar ahí: movería el precio contra sí mismo. Esa es la razón
estructural por la que la ineficiencia sobrevive, y es accesible a capital pequeño.

Pero el mismo estudio da la contrapartida:

> Descontando un coste del 3 %, el retorno medio baja de 5,2 % a 2,2 % y su intervalo de
> confianza **incluye el cero**.

De ahí la regla de diseño central del laboratorio: **el enemigo no es la competencia, es
el coste de ejecución.** La estrategia no se optimiza para acertar más, se optimiza para
operar menos y más barato.

---

## Las tres hipótesis candidatas

Un algoritmo no es efectivo por ser ingenioso, sino por explotar una ineficiencia concreta
que todavía existe. Estas son las candidatas que el laboratorio va a probar, cada una con
su razón estructural de supervivencia.

> **Decidido (2026-11-25):** se arranca con la hipótesis **A (PEAD)** sobre el universo
> **Russell 2000**, con horizonte **adaptativo con tope de ~21 días hábiles** y posiciones
> **largas y cortas** para medir alfa sin beta. El razonamiento completo de cada decisión,
> con lo que se descartó y por qué, está en
> **[docs/decisiones.md](docs/decisiones.md)**.

### A. Deriva post-resultados (PEAD) — *la primera que se probará*

**Hipótesis:** cuando una empresa publica resultados que sorprenden al mercado, el precio
no se ajusta de golpe: sigue derivando en la dirección de la sorpresa durante semanas.

**Por qué sobrevive:** exige procesar cientos de informes en las horas siguientes a su
publicación; es más fuerte en empresas pequeñas y poco cubiertas (~6 analistas frente a
~30 en large caps); y la deriva es lenta, así que no interesa al trading de alta frecuencia.

**Por qué encaja con un LLM:** la "sorpresa" relevante no es solo que el beneficio por
acción supere la estimación, es lo que dice el informe — cambios de guía, tono de la
dirección, riesgos nuevos. Eso es texto, y leer 400 informes el día que salen es
precisamente lo que un modelo de lenguaje hace bien y un humano no.

**Datos:** SEC EDGAR, gratuito.

### B. Compras de insiders en microcaps

**Hipótesis:** cuando un directivo compra acciones de su propia empresa con su dinero,
transmite información que el mercado tarda en incorporar.

**Por qué sobrevive:** límite de capacidad puro — no cabe capital institucional.

**Advertencia documentada:** es la hipótesis con la evidencia en contra más explícita. El
propio estudio que mide la señal concluye que con un 3 % de coste pierde la significancia
estadística. Se prueba sabiendo esto.

**Datos:** Formulario 4 de EDGAR, gratuito.

### C. Sobrerreacción a noticias y reversión

**Hipótesis:** los valores pequeños sobrerreaccionan a noticias negativas y revierten
parcialmente en los días siguientes.

**Por qué sobrevive:** pánico de inversores minoristas más iliquidez; el arbitrajista que
lo corregiría necesita asumir un riesgo que no le compensa en valores tan pequeños.

**Por qué encaja con un LLM:** requiere distinguir una noticia materialmente mala de ruido
con titular alarmante. Ningún indicador numérico hace ese juicio.

---

## El método de validación

Es la parte que casi nadie implementa y la que determina si un resultado significa algo.

### Deflated Sharpe Ratio

Si pruebas 500 variantes de una estrategia y te quedas con la mejor, su Sharpe está
inflado por selección. El DSR (Bailey y López de Prado) corrige por el número de pruebas,
la longitud de la muestra y la no-normalidad de los retornos, y devuelve la probabilidad
de que el resultado sea real. Por debajo de 0,95 no se puede descartar el azar.

### Longitud mínima de backtest

```
MinBTL ≈ 2·ln(N) / E[max_Sharpe]²
```

Con N = 1.000 configuraciones probadas y un Sharpe objetivo de 1,0: **~13,8 años de
datos** para que ese Sharpe no sea esperable por azar.

La implicación gobierna el proyecto entero: **cada combinación de parámetros que pruebas
consume credibilidad.** Un barrido de 10.000 combinaciones no es investigación, es generar
ruido con buen aspecto. Por eso el módulo `lab/journal.py` obliga a **declarar cada
hipótesis antes de ejecutarla**: ese contador es el `N` de la fórmula.

### Sin look-ahead, por construcción

La clase `PriceView` recorta la serie en el constructor y usa `__slots__`: no existe forma
de acceder a datos posteriores a la fecha de decisión. No es una convención que haya que
recordar, es una barrera que lanza `LookAheadError`.

---

## Arquitectura

```
trading-lab/
├── config.py          Todo parámetro que afecte a un resultado vive aquí
├── lab/
│   ├── data.py        Ingesta + PriceView (guardia anti-look-ahead)
│   ├── costs.py       Comisión + horquilla + deslizamiento, por broker
│   ├── backtest.py    Motor vectorizado (señal de T se ejecuta en T+1)
│   ├── metrics.py     Sharpe, drawdown, DSR, MinBTL
│   └── journal.py     Registro de experimentos en SQLite (el N del DSR)
├── tests/             El test anti-look-ahead es el más importante del repo
└── scripts/
    └── run_benchmark.py   Establece el rival a batir
```

### Dos reglas que no se negocian

1. **Las funciones de señal nunca pueden acceder a datos posteriores a la fecha que
   reciben.** Hay un test que lo verifica.
2. **`lab/journal.py` registra cada experimento antes de ejecutarlo.** Sin ese contador no
   se puede calcular el DSR, y sin DSR no se sabe si el resultado es real.

---

## Estado actual

**Fase 0 completa.** El laboratorio mide. Resultados reales del benchmark
(SPY, 2015-01-02 a 2026-11-24, 2.992 días):

| Escenario de costes | Retorno total | CAGR | Sharpe | Max drawdown | Costes |
|---|---|---|---|---|---|
| Sin costes (fantasía) | 325,10 % | 12,96 % | 0,81 | −32,05 % | 0,00 |
| Alpaca (0 % comisión) | 324,68 % | 12,95 % | 0,81 | −32,05 % | 10,00 |
| IBKR Europa (mín. 3 €) | 324,36 % | 12,95 % | 0,81 | −32,05 % | 17,50 |

**Ese Sharpe de 0,81 es el rival.** Cualquier estrategia que no lo supere *después de
costes*, en datos que no se usaron para ajustarla, es trabajo perdido.

Detalle instructivo: con **una sola operación**, la diferencia entre el escenario sin
costes y el más caro es de 17,50 € sobre 10.000 €. La fricción no se nota cuando no se
opera — y se vuelve letal cuando se opera a diario. El modelo de costes lo demuestra con
números en lugar de con una advertencia.

---

## Hoja de ruta

Cada fase tiene una condición de salida. Si no se cumple, el proyecto se detiene ahí, y
detenerse es un resultado válido.

| Fase | Qué se construye | Criterio para pasar | Estado |
|---|---|---|---|
| **0** | Ingesta sin look-ahead, modelo de costes, diario, benchmark | El benchmark está medido y los tests pasan | ✅ **Hecho** |
| **1** | PEAD sobre Russell 2000, largo-corto, con costes reales | Alfa significativa frente al mercado en 2023-2026, datos no usados para ajustar | 🔵 **Definida**, sin implementar |
| **2** | Capa LLM: análisis de informes y noticias | Mejora la fase 1 de forma medible. Si no, se descarta: es coste sin alfa | ⬜ |
| **3** | Paper trading en vivo, 3-6 meses | Resultados coherentes con el backtest | ⬜ |
| **4** | Decisión informada sobre capital real | — | ⬜ |

La fase 3 es la que todo el mundo se salta y la que de verdad decide. Son meses, no días:
hacen falta suficientes operaciones para distinguir habilidad de suerte.

---

## Stack

| Capa | Elección | Coste |
|---|---|---|
| Lenguaje | Python 3.14 (`pandas`, `numpy`, `scipy`) | 0 € |
| Motor de backtest | Propio, ~60 líneas legibles | 0 € |
| Broker | Alpaca *paper trading*, datos de mercado reales | 0 € |
| Precios | `yfinance` → Alpaca market data | 0 € |
| Texto financiero | SEC EDGAR (informes, Formulario 4, 13F) | 0 € |
| Extracción masiva | Claude Haiku 5.5 vía Batch API (−50 %) | ~0,03 $/noche |
| Decisión y síntesis | Claude Opus 5.5 vía Batch API (−50 %) | ~0,80 $/ejecución |

Arquitectura de IA en dos niveles por una razón de coste: el modelo barato filtra cientos
de documentos, el capaz solo juzga las pocas candidatas que pasan el filtro. Con 2-3
ejecuciones semanales, la capa de IA cuesta del orden de **7-8 $/mes**.

> Nota deliberada: `vectorbt` y `backtrader` no son dependencias. Son buenos motores, pero
> `vectorbt` depende de `numba`, que tarda en soportar versiones nuevas de Python, y para
> la fase 0 un motor propio de 60 líneas legibles vale más que uno opaco de 60.000. Se
> incorporarán cuando el barrido de parámetros lo justifique.

---

## Ejecutar

```bash
git clone https://github.com/Hugoramos-tech/trading-lab.git
cd trading-lab
python -m pip install -r requirements.txt

python -m pytest tests/ -q          # 10 tests, incluido el anti-look-ahead
python scripts/run_benchmark.py     # establece el rival a batir
```

---

## Documentación

| Documento | Contenido |
|---|---|
| **[docs/glosario.md](docs/glosario.md)** | Todo término de mercados del repo explicado desde cero: Sharpe, drawdown, alfa y beta, horquilla, look-ahead, sobreajuste, PEAD, límites al arbitraje. Con números de referencia para calibrar qué es bueno y qué es sospechoso |
| **[docs/decisiones.md](docs/decisiones.md)** | Registro vivo de decisiones de diseño: qué se decidió, por qué, qué se descartó, preguntas abiertas y riesgos conocidos del plan |

---

## Bibliografía

**Sobre agentes LLM en trading**
- [The Alpha Illusion: Reported Alpha from LLM Trading Agents Should Not Be Treated as Deployment Evidence](https://arxiv.org/html/2605.16895v1)
- [LLM Trading Agents Earn Beta, Not Alpha: A Look-Ahead-Free Benchmark](https://arxiv.org/html/2611.19530)
- [Evaluating LLM Trading Agents: A Critical Review of Backtesting Validity](https://arxiv.org/html/2611.24133)
- [Can LLM-based Financial Investing Strategies Outperform the Market in Long Run?](https://www.alphaxiv.org/abs/2505.07078)
- [TradingAgents: Multi-Agents LLM Financial Trading Framework](https://arxiv.org/pdf/2412.20138) (el original)

**Sobre validación y sobreajuste**
- [The Deflated Sharpe Ratio — Bailey & López de Prado](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551)
- [The Dangers of Backtesting](https://portfoliooptimizationbook.com/book/8.3-dangers-backtesting.html)

**Sobre decaimiento de anomalías**
- [Does Academic Research Destroy Stock Return Predictability? — McLean & Pontiff](https://www.researchgate.net/publication/254926004_Does_Academic_Research_Destroy_Stock_Return_Predictability)
- [Anomalies across the globe — Jacobs & Müller](https://www.unicreditgroup.eu/content/dam/unicreditgroup-eu/ucfoundation/WorkingPapers/2019/wp-135-Jacobs-e-Mueller.pdf)
- [Publication Bias in Asset Pricing Research](https://arxiv.org/pdf/2209.13623)

**Sobre límites al arbitraje**
- [Insider Purchases Far Below the 52-Week High: Microcap Equities](https://arxiv.org/pdf/2602.06198)

---

## Aviso

Este repositorio es un proyecto de **investigación y aprendizaje**. No es asesoramiento
financiero ni una recomendación de inversión, y nada de lo que contiene debe usarse para
operar con dinero real sin entender los riesgos.

Contexto que conviene tener presente: entre el **89 % y el 97 %** de los traders
minoristas que persisten pierden dinero (SEBI India: 93 % en tres años; estudio de São
Paulo sobre futuros: 97 % de quienes aguantaron más de 300 días), y los brókeres europeos
están obligados a declarar que entre el 74 % y el 89 % de las cuentas minoristas pierde
dinero. Un sistema bien construido no cambia esas probabilidades por sí solo; sirve para
saber, antes de arriesgar nada, si una idea tiene fundamento.

## Licencia

MIT — ver [LICENSE](LICENSE).
