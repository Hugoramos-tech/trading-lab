# Glosario

Todo término de mercados que aparece en este repositorio, explicado desde cero.
Si lees algo en el código o en el README y no sabes qué es, está aquí.

---

## 1. Lo básico

**Acción.** Una participación en la propiedad de una empresa. Si compras una acción de
Apple, eres dueño de una fracción minúscula de Apple.

**Posición.** Cuánto tienes invertido en algo ahora mismo. En este laboratorio la posición
se expresa de 0 a 1: `0` es estar fuera (todo en efectivo), `1` es estar completamente
invertido, `0.5` es la mitad.

**Ir largo / ir corto.** Largo es lo normal: compras esperando que suba. Corto es apostar
a que baja (pides prestada la acción, la vendes, y la recompras más barata). Este proyecto
solo opera largo: ir corto añade riesgos que no tocan todavía.

**Ticker.** El código corto de un valor en bolsa. `SPY`, `AAPL`, `TSLA`.

**Comprar y mantener** (*buy and hold*). Comprar y no volver a tocarlo. Suena simple y por
eso es tramposo: es el rival contra el que se compara todo, y gana a la mayoría de las
estrategias activas.

**S&P 500 / SPY.** El S&P 500 es un índice: la media de las 500 empresas más grandes de
EEUU. `SPY` es un fondo cotizado que lo replica, así que comprar SPY equivale a comprar
"el mercado americano entero". Es el benchmark estándar.

**Benchmark.** La referencia contra la que mides. Si tu estrategia rinde un 8 % y el
mercado hizo un 13 %, tu estrategia es mala aunque ganara dinero.

---

## 2. Cómo se mide si una estrategia va bien

**Retorno total.** Cuánto ha crecido el dinero, en porcentaje. De 10.000 a 42.500 es un
325 %.

**CAGR** (*Compound Annual Growth Rate*, rentabilidad anualizada compuesta). El mismo
retorno, pero expresado como "cuánto ganó al año de media". Un 325 % en 11,9 años es un
12,96 % anual. Sirve para comparar periodos de distinta duración.

**Volatilidad.** Cuánto oscila el precio. Alta volatilidad = sube y baja mucho. Se expresa
como porcentaje anual: el S&P 500 ronda el 17 %.

**Sharpe ratio.** La métrica central de todo esto. Es **rentabilidad dividida por
volatilidad**: cuánto ganas por cada unidad de sobresalto que soportas.

> Analogía: dos rutas te llevan al mismo sitio en el mismo tiempo, pero una es una
> autopista y la otra una pista de montaña con precipicios. Misma rentabilidad, Sharpe muy
> distinto.

Números de referencia para calibrar el oído:

| Sharpe | Qué significa |
|---|---|
| 0,5 - 0,8 | El mercado comprando y manteniendo. **SPY da 0,81 en nuestro benchmark** |
| 1,0 | Bueno de verdad. Muchos fondos profesionales no llegan |
| > 2,0 | En un backtest casero: casi siempre un error o sobreajuste, no un hallazgo |

**Drawdown** (caída máxima). Lo que pierdes desde el punto más alto hasta el más bajo
siguiente. Si tu cartera llega a 10.000, baja a 6.800 y luego recupera, tuviste un
drawdown del −32 %. Es la métrica que mide el dolor real: el 325 % de SPY vino con un
−32 % en 2020 que había que aguantar sin vender.

---

## 3. Alfa y beta

Dos palabras que se usan constantemente y que conviene no confundir.

**Beta.** La parte de tus resultados que viene de estar expuesto al mercado. Si el mercado
sube un 10 % y tú subes un 10 %, eso es beta: no has hecho nada especial, has estado
dentro.

**Alfa.** La parte que viene de tu habilidad, por encima del mercado. Es lo que de verdad
intentas conseguir, y es lo difícil.

> Por qué importa aquí: el estudio *LLM Trading Agents Earn Beta, Not Alpha* midió agentes
> de IA que parecían ganar dinero, y descubrió que todos sus resultados se explicaban por
> estar invertidos en un mercado que subía. Ninguno aportaba habilidad. Es como presumir
> de mojarte bajo la lluvia.

---

## 4. Lo que te cuesta operar (la fricción)

Implementado en [`lab/costs.py`](../lab/costs.py).

**Comisión.** Lo que te cobra el bróker por ejecutar una orden. Puede ser un porcentaje
(0,05 %), una cantidad fija, o un porcentaje **con un mínimo** — y ese mínimo es el que
arruina cuentas pequeñas: 3 € de mínimo sobre una posición de 25 € es un 12 % por orden,
24 % contando la ida y la vuelta.

**Horquilla** (*spread*). En cualquier momento hay dos precios: lo que te pagan si vendes
(oferta) y lo que te cobran si compras (demanda). La diferencia es la horquilla, y la
pagas en cada operación sin que aparezca en ninguna factura. Es el coste invisible.

**Deslizamiento** (*slippage*). El precio se mueve entre que decides comprar y que la
orden se ejecuta. Siempre un poco en tu contra.

**Punto básico** (*bps*). Una centésima de porcentaje. 10 bps = 0,10 %. Se usa porque
hablar de "0,0010" es incómodo.

**Breakeven** (punto de equilibrio). Cuánto tiene que subir el precio para que, después de
pagar todo lo anterior, no hayas perdido dinero. Lo calcula
`CostModel.breakeven_pct()`, y es la prueba de realidad de cualquier estrategia: si tu
ganancia media por operación no supera ese número, pierdes dinero operando.

---

## 5. Horizontes temporales

**Intradía** (*day trading*). Abrir y cerrar el mismo día. Muchas operaciones, mucha
fricción. Descartado en este proyecto: el coste por operación se come cualquier ventaja, y
además una llamada a un modelo de lenguaje tarda segundos.

**Swing trading.** Mantener de días a semanas. Es el horizonte de este laboratorio: pocas
operaciones (poca fricción) y tiempo suficiente para que un análisis de texto aporte algo.

**Largo plazo.** Meses o años. Es donde comprar y mantener gana casi siempre.

**Paper trading.** Operar con dinero ficticio pero precios reales y en tiempo real. Es el
banco de pruebas honesto: todo lo que pasaría de verdad, salvo perder dinero.

---

## 6. Tamaño de empresa y liquidez

**Capitalización** (*market cap*). El valor total de una empresa en bolsa: precio de la
acción × número de acciones.

| Categoría | Tamaño aproximado |
|---|---|
| *Large cap* | Más de 10.000 M$ (Apple, Microsoft) |
| *Small cap* | Entre 300 M$ y 2.000 M$ |
| *Microcap* | Menos de 250 M$ (definición de FINRA, no oficial) |

**Liquidez / volumen.** Cuánto se negocia al día. Si una empresa mueve 100.000 $ diarios y
quieres comprar 50.000 $, tu propia orden empuja el precio hacia arriba y acabas pagando
más de lo que viste. Eso es **impacto de mercado**.

> Esta es la clave de todo el proyecto: un fondo con 500 millones **no puede** operar
> microcaps, porque no le cabe. En el 53,3 % de los casos estudiados, una orden de
> 50.000 $ ya supera el 5 % del volumen diario. Un inversor pequeño sí entra ahí. Tu
> ventaja no es ser más listo, es ser más pequeño.

---

## 7. Los errores que te hacen creer que funciona

Esta sección es la razón de existir del laboratorio.

**Backtest.** Simular una estrategia sobre datos históricos para ver qué habría pasado.
Imprescindible y profundamente engañoso si se hace mal.

**Sesgo de anticipación** (*look-ahead bias*). Usar, al decidir en una fecha, información
que todavía no existía entonces. Es el error número uno, y casi siempre es accidental:
calcular un indicador sobre toda la serie, usar el precio de cierre de hoy para "decidir"
una compra de hoy, usar datos que luego fueron corregidos.

> En este repo no se confía en la buena memoria: la clase `PriceView` recorta la serie en
> el constructor y usa `__slots__`, así que el objeto **no contiene** el futuro. Pedirlo
> lanza `LookAheadError`. Es una barrera, no una convención.

**Sobreajuste** (*overfitting*). Probar tantas variantes que acabas encontrando una que
funciona de maravilla... en ese histórico concreto y por casualidad. Es el equivalente a
tirar 10.000 monedas y presentar la que salió cara 15 veces seguidas como moneda mágica.

**Deflated Sharpe Ratio (DSR).** El antídoto. Corrige el Sharpe por el número de pruebas
que hiciste, la longitud de los datos y la forma de la distribución, y devuelve **la
probabilidad de que el resultado sea real**. Por debajo de 0,95, no puedes descartar el
azar. Implementado en [`lab/metrics.py`](../lab/metrics.py).

**MinBTL** (longitud mínima de backtest). Cuántos años de datos necesitas para que un
resultado sea creíble, dado cuántas cosas probaste. Con 1.000 configuraciones probadas y
un Sharpe objetivo de 1,0 hacen falta ~13,8 años. Dicho de otro modo: **cada prueba que
haces consume credibilidad.**

**Walk-forward.** Avanzar por la historia simulando el presente: ajustas con datos hasta
2020, pruebas en 2021; ajustas hasta 2021, pruebas en 2022. Así el test siempre usa datos
que la estrategia no vio al ajustarse.

**Fuera de muestra** (*out-of-sample*). Datos que no se usaron para diseñar ni ajustar la
estrategia. Es el único resultado que cuenta.

**Contaminación temporal.** Problema específico de los modelos de lenguaje: si pruebas una
estrategia sobre 2023 usando un modelo entrenado con datos de hasta 2024, el modelo puede
"recordar" lo que pasó. No está prediciendo, está repitiendo. FinMem perdió el 72 % de su
rentabilidad cuando se probó en un periodo posterior a su entrenamiento.

---

## 8. De dónde salen los datos

**EDGAR.** El archivo público de la SEC (el regulador de los mercados de EEUU). Todas las
empresas cotizadas están obligadas a publicar ahí. Es gratuito y sin límites de pago: es
la mejor fuente de texto financiero del mundo, y la razón por la que este proyecto trabaja
con el mercado estadounidense.

**10-K / 10-Q.** El informe anual y el trimestral de una empresa. Cuentas, riesgos y
explicaciones de la dirección.

**Resultados** (*earnings*). La publicación trimestral de cuánto ha ganado una empresa. Es
el momento de máxima información nueva, y el que ancla la hipótesis principal del
proyecto.

**Formulario 4** (*Form 4*). Cuando un directivo o consejero compra o vende acciones de su
propia empresa, debe declararlo en pocos días. Señal interesante: nadie conoce la empresa
mejor que ellos.

**13F.** La declaración trimestral de los grandes gestores con sus posiciones. **Se
publica con 45 días de retraso**, así que sirve para estudiar, no para copiar: cuando la
lees, el precio ya se movió.

---

## 9. Ineficiencias de mercado

**Ineficiencia.** Un patrón en los precios que permitiría ganar dinero de forma repetible.
La teoría dice que no deberían existir porque alguien las explotaría hasta agotarlas — y
en general es verdad, lo que hace que las supervivientes sean valiosas.

**Límites al arbitraje.** La razón por la que una ineficiencia sobrevive: alguien podría
corregirla, pero no puede o no le compensa. Falta de capacidad (no le cabe el dinero),
coste de operar, riesgo que no puede asumir, o que es demasiado pequeña para molestarse.

> Regla práctica de este proyecto: si no puedes explicar **por qué nadie se ha comido ya**
> tu ineficiencia, probablemente ya se la comieron.

**Decaimiento de anomalías.** Las ineficiencias publicadas se desgastan. McLean & Pontiff
midieron una caída del ~26 % fuera de muestra y otro ~58 % después de publicarse. De ahí
que las estrategias de los libros y los blogs no sirvan: están publicadas.

**PEAD** (*Post-Earnings Announcement Drift*, deriva post-resultados). La hipótesis
principal del proyecto: cuando una empresa publica resultados que sorprenden, el precio no
se ajusta de golpe, sino que sigue derivando en esa dirección durante semanas. Sobrevive
porque exige leer cientos de informes el día que salen, es más fuerte en empresas poco
cubiertas por analistas, y es demasiado lenta para interesar al trading de alta frecuencia.

**Reversión a la media.** La idea de que lo que se ha movido demasiado tiende a volver.
Base de la hipótesis C: los valores pequeños sobrerreaccionan a malas noticias y luego
recuperan parte del golpe.

---

## 10. Cosas que es mejor saber antes

**Apalancamiento.** Operar con dinero prestado para multiplicar la exposición. Multiplica
las ganancias y las pérdidas por igual, y permite perder más de lo que pusiste. Es la vía
rápida para multiplicar una cuenta pequeña, y también la razón por la que esas cuentas
desaparecen.

**CFD.** Un derivado que replica el precio de un activo sin que lo poseas, casi siempre
apalancado. Los brókeres europeos están obligados a declarar qué porcentaje de sus
clientes minoristas pierde dinero: oscila entre el 74 % y el 89 %.

**Regla PDT** (*Pattern Day Trader*). Norma de FINRA en EEUU: con menos de 25.000 $ en una
cuenta de margen, no puedes hacer más de 3 operaciones intradía en 5 días hábiles. No
aplica en paper trading, pero condiciona cualquier plan real.

**FIFO** (*First In, First Out*). Regla fiscal española: al vender, Hacienda considera que
vendes primero las acciones que compraste primero, y se aplica **por ISIN sobre todo tu
patrimonio**, sin importar el bróker. Con operaciones frecuentes, llevar esa contabilidad
es tan trabajoso como la estrategia.

---

## Para seguir leyendo

La bibliografía completa, con enlaces a los papers citados aquí, está al final del
[README](../README.md).
