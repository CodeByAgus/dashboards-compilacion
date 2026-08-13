# Dashboard — Análisis de Criptomonedas

**Pregunta de negocio:** ¿Cuál es la performance histórica de las principales criptomonedas y cómo se comparan en retorno, volatilidad y volumen?

**Autor:** Agustín Mendoza  
**Herramientas:** Python · pandas · Power BI · DAX

---

## Dataset
**Cryptocurrency Price History** — sudalairajkumar (Kaggle)  
https://www.kaggle.com/datasets/sudalairajkumar/cryptocurrencypricehistory

Criptomonedas incluidas: Bitcoin · Ethereum · BNB · XRP · Cardano · Solana · Dogecoin · Polkadot

---

## Cómo preparar los datos

```bash
pip install pandas numpy openpyxl
python preparar_datos.py
```

Genera 3 Excel en `data/powerbi/` listos para importar a Power BI.

---

## Modelo de datos en Power BI

```
historico_precios  ──┐
                     ├── (crypto) ── resumen_cryptos
volumen_mensual   ───┘
```

---

## Visualizaciones — 4 páginas

### Página 1 — Resumen General
| Visual | Campos |
|--------|--------|
| Tarjetas KPI | precio_actual · retorno_30d_pct · retorno_1a_pct · volatilidad_prom |
| Barras horizontales | retorno_1a_pct por crypto (ordenado desc) |
| Tabla con formato condicional | resumen_cryptos completo |
| Segmentador | crypto (multi-select) |

### Página 2 — Evolución de Precios
| Visual | Campos |
|--------|--------|
| Líneas | fecha vs close por crypto |
| Líneas | fecha vs retorno_acumulado_pct (base 100) |
| Tarjetas | max_historico · min_historico · max_52s |
| Segmentador | fecha (rango) · crypto |

### Página 3 — Volatilidad y Riesgo
| Visual | Campos |
|--------|--------|
| Líneas | fecha vs volatilidad_30d por crypto |
| Scatter | retorno_1a_pct (X) vs volatilidad_prom (Y) — tamaño = volumen |
| Distribución | retorno_diario_pct por crypto |

### Página 4 — Volumen de Mercado
| Visual | Campos |
|--------|--------|
| Columnas apiladas | mes vs volumen_total por crypto |
| Líneas | precio_promedio mensual |
| Matriz (heatmap) | anio × mes_nombre vs retorno_30d_pct |

---

## Medidas DAX principales

```dax
Precio Actual =
CALCULATE(
    LASTNONBLANK(historico_precios[close], 1),
    ALLEXCEPT(historico_precios, historico_precios[crypto])
)

Retorno Período % =
VAR precio_inicio = CALCULATE(FIRSTNONBLANK(historico_precios[close], 1))
VAR precio_fin    = CALCULATE(LASTNONBLANK(historico_precios[close], 1))
RETURN DIVIDE(precio_fin - precio_inicio, precio_inicio) * 100

Volatilidad Promedio =
AVERAGE(historico_precios[volatilidad_30d])

Máximo Período =
MAXX(historico_precios, historico_precios[high])
```

---

## Estructura del proyecto
```
proyecto_powerbi_crypto/
├── preparar_datos.py
├── README.md
├── data/
│   ├── raw/       <- CSV de Kaggle (Bitcoin.csv, Ethereum.csv, etc.)
│   └── powerbi/   <- Excel para Power BI
│       ├── historico_precios.xlsx
│       ├── resumen_cryptos.xlsx
│       └── volumen_mensual.xlsx
└── capturas/      <- screenshots del dashboard
```
