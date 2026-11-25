# Registro de decisiones

Documento vivo. Recoge **qué se ha decidido, por qué, y qué queda abierto**, para poder
retomar el proyecto en cualquier momento sin reconstruir el razonamiento desde cero.

Última actualización: **2026-11-25**

---

## Estado del proyecto

| | |
|---|---|
**Fase actual** | 0 completada. Fase 1 definida, sin empezar a implementar |
**Benchmark a batir** | SPY 2015-2026: **Sharpe 0,81**, CAGR 12,96 % |
**Experimentos declarados (N)** | 1 (solo el benchmark) |

---

## D1 — Hipótesis: deriva post-resultados (PEAD)

**Decidido:** hipótesis A.

> Cuando una empresa publica resultados que sorprenden al mercado, el precio no se ajusta
> de golpe: sigue derivando en la dirección de la sorpresa durante semanas.

**Por qué esta y no las otras dos:**

- Es la que tiene mejor evidencia académica y la más replicada.
- Su razón estructural de supervivencia es sólida: exige procesar cientos de informes en
  las horas siguientes a su publicación, es más fuerte en empresas poco cubiertas por
  analistas, y la deriva es demasiado lenta para interesar al trading de alta frecuencia.
- Es **la única de las tres donde un LLM aporta algo que ningún indicador numérico puede**:
  la sorpresa relevante no es solo que el beneficio por acción supere la estimación, es lo
  que *dice* el informe — cambios de guía, tono de la dirección, riesgos nuevos.

**Descartadas, con su motivo:**

- **B (compras de insiders en microcaps):** razón estructural más limpia, pero el propio
  estudio que mide la señal concluye que con un coste del 3 % pierde la significancia
  estadística. Queda como candidata futura.
- **C (sobrerreacción a noticias):** la más intuitiva, pero exige definir qué cuenta como
  "noticia mala", y esa definición introduce juicio subjetivo difícil de validar.

---

## D2 — Universo: Russell 2000

**Decidido:** empresas pequeñas de EEUU (índice Russell 2000).

El compromiso es que **ineficiencia y coste de operar van en direcciones opuestas**:

| Universo | Ineficiencia | Coste | Datos | Veredicto |
|---|---|---|---|---|
S&P 500 | Casi nula: ~30 analistas por empresa | Mínimo | Impecables | Descartado: el PEAD está agotado ahí |
**Russell 2000** | **Real: ~6 analistas por empresa** | **Moderado** | **Buenos** | **Elegido** |
Microcaps (<250 M$) | Máxima | Letal (3 % anula la señal) | Con huecos | Descartado por coste y calidad |

Es el punto donde hay ineficiencia aprovechable y el coste sigue siendo pagable.

---

## D3 — Horizonte: adaptativo, con tope de ~21 días hábiles

**Decidido:** mantener mientras la deriva continúe, con un límite máximo de
aproximadamente un mes natural (**21 días hábiles**).

Esto es más ambicioso que un horizonte fijo y tiene un coste estadístico que hay que
gestionar: **una regla de salida adaptativa añade parámetros, y cada parámetro es un grado
de libertad más para engañarse** (ver MinBTL en el glosario). Por eso se implementa en dos
pasos, no en uno:

1. **Línea base sin parámetros extra:** salida fija a 21 días hábiles. Se mide también a
   5 y 60 días, no para elegir el mejor, sino para ver **la forma de la curva de decaimiento
   de la señal**. Eso es información sobre el fenómeno, no un barrido de optimización.
2. **Una sola regla adaptativa**, comparada contra esa línea base. Si no la mejora de forma
   medible, se descarta: habrá añadido complejidad sin añadir valor.

Candidatas para la regla adaptativa, por orden de parsimonia (de menos a más parámetros):

| Regla | Parámetros | Idea |
|---|---|---|
Agotamiento de la deriva | 1 | Salir si el precio deja de avanzar durante N días |
Trailing stop | 1 | Salir si cae un X % desde el máximo alcanzado en la posición |
Invalidación por noticia | — | Salir si aparece información nueva que contradice la tesis (aquí vuelve a entrar el LLM) |

**Pendiente de decidir:** cuál de las tres, cuando la línea base esté medida. No antes:
sin línea base no hay nada contra lo que comparar.

---

## D4 — Dirección: largo y corto

**Decidido:** comprar las sorpresas positivas **y vender en corto** las negativas.

**Por qué es la elección correcta para medir:** si compras las buenas y vendes las malas a
la vez, el movimiento general del mercado se cancela — si todo sube, ganas en las largas y
pierdes en las cortas. Lo que queda es puramente la capacidad de distinguir unas de otras,
es decir **alfa puro, sin beta**. Es exactamente lo que el laboratorio quiere medir, y es
una posición más honesta que la alternativa.

**El problema que trae, y cómo se gestiona:**

Ponerse corto exige que alguien te preste las acciones, y en empresas pequeñas eso a
menudo es caro o simplemente no hay existencias disponibles.

- **En el laboratorio (fases 1 y 2) no es un problema:** el backtest y el paper trading no
  tienen restricción de préstamo, así que la medición de alfa limpio se puede hacer sin
  obstáculos. Esto es precisamente lo que buscábamos.
- **En la fase 3 sí hay que verificarlo:** la API de Alpaca expone si un valor es *easy to
  borrow*. Habrá que filtrar el universo por disponibilidad real de préstamo y añadir el
  coste de préstamo al modelo de costes, o la pata corta será una ficción.
- **Riesgo:** una posición corta tiene pérdida teórica sin techo (si la acción se triplica,
  pierdes el triple). El módulo de riesgo debe limitar el tamaño de las cortas con un stop
  obligatorio, no opcional.

**Tareas que esta decisión añade:**

- [ ] Añadir coste de préstamo (*borrow fee*) a `lab/costs.py`
- [ ] Soportar posiciones negativas en `lab/backtest.py` (hoy solo admite 0 a 1)
- [ ] Filtro de disponibilidad de préstamo antes de la fase 3
- [ ] Stop obligatorio en cortas en el módulo de riesgo

---

## Decisiones técnicas tomadas sin consulta (y su justificación)

**Periodo de datos: 2015-2026** (~11 años). No es arbitrario: el presupuesto de pruebas
que permite el MinBTL depende de la longitud de la muestra. Con ~11 años y un Sharpe
objetivo de 1,0, el margen para probar configuraciones sin caer en sobreajuste es del
orden de unos cientos, no de miles.

**División de datos:**

| Tramo | Años | Uso |
|---|---|---|
Ajuste (*in-sample*) | 2015 - 2022 | Diseñar y afinar. Se puede mirar cuanto se quiera |
Prueba (*out-of-sample*) | 2023 - 2026 | **No se mira hasta el final.** Una sola vez |

Esa regla de "una sola vez" es la que da validez al resultado. Mirar el tramo de prueba,
ajustar algo, y volver a mirarlo lo convierte en tramo de ajuste y destruye la medición.

**Mercado estadounidense y no español:** SEC EDGAR es la mejor fuente gratuita de texto
financiero que existe, y es lo que alimenta la capa LLM. La CNMV no tiene equivalente
comparable en cobertura ni en formato.

---

## Preguntas abiertas — respondidas el 2026-11-25

| Pregunta | Respuesta | Consecuencia |
|---|---|---|
| Cuenta de Alpaca | **No existe** | Crearla al inicio de la fase 1. Verificar de paso que admite residentes en España: las comparativas la recomiendan pero ninguna lo confirma |
| Clave de API de Anthropic | **Probablemente sí**, sin confirmar | Verificar con `ant auth status` o en la consola de Anthropic. No bloquea: no se necesita hasta la fase 2 |
| Nivel de `pandas` | **Ninguno** | **Es el dato que más afecta al plan.** Ver abajo |
| Dedicación semanal | Bastantes horas | El plan de meses es viable |
| Investigar la fuente del calendario de resultados | **Aplazado** a la próxima sesión de trabajo | Es la primera tarea pendiente |

### Consecuencia del nivel de pandas

`pandas` es la librería que sostiene todo el proyecto: toda la ingesta, el motor de
backtest y las métricas están escritos sobre ella. Partir de cero no es un obstáculo, pero
sí obliga a añadir un paso previo a la fase 1.

**Decisión:** no un tutorial genérico, sino familiarización **sobre los datos del propio
proyecto** — la serie de SPY que ya está descargada en `cache/`. Conceptos imprescindibles
y suficientes para seguir el código existente:

- `DataFrame` y `Series`: la tabla y la columna
- Índice de fechas: seleccionar por rango, que es la base de `PriceView`
- `pct_change()`, `rolling()`, `shift()`: retornos, medias móviles y el desplazamiento
  temporal que impide mirar el futuro
- `groupby()` y `merge()`: necesarios en la fase 1 para cruzar eventos de resultados con
  precios

Ese último punto, `merge` sobre fechas, es el que de verdad hará falta para la hipótesis
PEAD: cruzar "qué día publicó resultados cada empresa" con "cómo se movió su precio
después".

---

## Punto de retomada

**Lo siguiente, en este orden:**

1. **Investigar la fuente de datos de resultados** (aplazado por decisión de Hugo). Hay que
   localizar, para el Russell 2000: fechas de publicación de resultados, y estimaciones de
   consenso de analistas o un sustituto. **Es el riesgo número uno del proyecto**: si no hay
   fuente gratuita, la hipótesis PEAD clásica no se puede medir y hay que pasar al plan
   alternativo (definir la sorpresa con el LLM a partir del propio informe, sin consenso).
2. **Crear la cuenta de Alpaca** y guardar las claves en `.env` (ya está en `.gitignore`).
3. **Paso de familiarización con pandas** sobre los datos de `cache/`.
4. Solo entonces: implementar la señal de la fase 1.

**Estado del código:** fase 0 completa y funcionando. 10 tests en verde.
`python scripts/run_benchmark.py` reproduce el benchmark en cualquier momento.

---

## Riesgos conocidos del plan

| Riesgo | Impacto | Mitigación |
|---|---|---|
Las estimaciones de analistas para small caps pueden no estar disponibles gratis | **Alto** — sin ellas no se puede medir la "sorpresa" de forma clásica | Alternativa: definir la sorpresa a partir del propio informe con el LLM, sin estimación de consenso. Es menos estándar pero más original, y es justo donde el LLM aporta |
Supervivencia del sesgo del índice (*survivorship bias*): el Russell 2000 de hoy no incluye las empresas que quebraron | Medio — infla los resultados | Usar la composición histórica del índice, o aceptar y documentar el sesgo |
`numba` sin soporte para Python 3.14 bloquea `vectorbt` | Bajo | Motor propio ya implementado; no es dependencia |
La pata corta no es ejecutable en real por falta de préstamo | Medio — reduciría la estrategia a solo largo | Verificar disponibilidad en fase 3 y medir el impacto de restringirse a valores prestables |

---

## Histórico de cambios

| Fecha | Cambio |
|---|---|
2026-11-25 | Fase 0 completada: ingesta, costes, motor, métricas, diario, benchmark |
2026-11-25 | Glosario de mercados añadido |
2026-11-25 | Decisiones D1-D4 tomadas. Fase 1 definida, pendiente de resolver las preguntas abiertas |
| 2026-11-25 | Preguntas abiertas respondidas. Se anade paso de familiarizacion con pandas. Proxima tarea: investigar la fuente de datos de resultados |
