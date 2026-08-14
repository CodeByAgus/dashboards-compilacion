import pandas as pd
import numpy as np
import os

for carpeta in ['data/raw', 'data/powerbi']:
    os.makedirs(carpeta, exist_ok=True)

CRYPTOS = ['Bitcoin', 'Ethereum', 'BNB', 'XRP', 'Cardano', 'Solana', 'Dogecoin', 'Polkadot']


def cargar_csv_crypto(nombre, ruta='data/raw/'):
    archivo = f'{ruta}{nombre}.csv'
    if not os.path.exists(archivo):
        print(f'[SKIP] No encontrado: {archivo}')
        return None
    df = pd.read_csv(archivo)
    df['crypto'] = nombre
    return df


def limpiar_dataframe(df):
    df = df.copy()
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

    col_fecha = next((c for c in df.columns if 'date' in c or 'time' in c), None)
    if col_fecha:
        df['fecha'] = pd.to_datetime(df[col_fecha], errors='coerce')
        df = df.dropna(subset=['fecha'])
        df = df.sort_values('fecha')

    for col in ['open', 'high', 'low', 'close', 'volume', 'market_cap', 'marketcap']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')

    return df


def calcular_metricas(df):
    df = df.copy()

    df['retorno_diario_pct'] = df.groupby('crypto')['close'].pct_change() * 100
    df['retorno_7d_pct']     = df.groupby('crypto')['close'].pct_change(7) * 100
    df['retorno_30d_pct']    = df.groupby('crypto')['close'].pct_change(30) * 100

    df['max_52s'] = df.groupby('crypto')['high'].transform(lambda x: x.rolling(365, min_periods=1).max())
    df['min_52s'] = df.groupby('crypto')['low'].transform(lambda x: x.rolling(365, min_periods=1).min())

    df['volatilidad_30d'] = df.groupby('crypto')['retorno_diario_pct'].transform(
        lambda x: x.rolling(30, min_periods=5).std()
    )

    df['anio']       = df['fecha'].dt.year
    df['mes']        = df['fecha'].dt.month
    df['mes_nombre'] = df['fecha'].dt.strftime('%b')
    df['trimestre']  = df['fecha'].dt.quarter

    return df


def calcular_retorno_acumulado(df):
    resultado = []
    for crypto, grupo in df.groupby('crypto'):
        grupo = grupo.sort_values('fecha').copy()
        precio_inicio = grupo['close'].iloc[0]
        grupo['retorno_acumulado_pct'] = (grupo['close'] / precio_inicio - 1) * 100
        resultado.append(grupo)
    return pd.concat(resultado, ignore_index=True)


def construir_tabla_resumen(df):
    ultima_fecha = df['fecha'].max()
    hace_30d     = ultima_fecha - pd.Timedelta(days=30)
    hace_365d    = ultima_fecha - pd.Timedelta(days=365)

    def resumen_crypto(grupo):
        ultimo    = grupo[grupo['fecha'] == grupo['fecha'].max()]
        hace30    = grupo[grupo['fecha'] >= hace_30d]
        hace365   = grupo[grupo['fecha'] >= hace_365d]

        precio_actual = ultimo['close'].values[0] if len(ultimo) else np.nan
        precio_30d    = hace30['close'].iloc[0]   if len(hace30)  else np.nan
        precio_365d   = hace365['close'].iloc[0]  if len(hace365) else np.nan

        return pd.Series({
            'precio_actual':       round(precio_actual, 4),
            'retorno_30d_pct':     round((precio_actual / precio_30d - 1) * 100, 2)  if precio_30d  else np.nan,
            'retorno_1a_pct':      round((precio_actual / precio_365d - 1) * 100, 2) if precio_365d else np.nan,
            'volatilidad_prom':    round(grupo['volatilidad_30d'].mean(), 2),
            'max_historico':       round(grupo['high'].max(), 4),
            'min_historico':       round(grupo['low'].min(), 4),
            'volumen_prom_diario': round(grupo['volume'].mean(), 0) if 'volume' in grupo.columns else np.nan,
        })

    return df.groupby('crypto').apply(resumen_crypto).reset_index()


def main():
    frames = []
    for nombre in CRYPTOS:
        df = cargar_csv_crypto(nombre)
        if df is not None:
            frames.append(df)

    if not frames:
        print('No se encontraron archivos CSV.')
        print('Descargá el dataset: https://www.kaggle.com/datasets/sudalairajkumar/cryptocurrencypricehistory')
        print('Copiá los CSV a data/raw/ con el nombre de cada crypto (ej: Bitcoin.csv)')
        return

    df_raw = pd.concat(frames, ignore_index=True)
    df_raw = limpiar_dataframe(df_raw)
    print(f'Total registros cargados: {len(df_raw):,}')

    df = calcular_metricas(df_raw)
    df = calcular_retorno_acumulado(df)
    df_resumen = construir_tabla_resumen(df)

    cols = ['fecha', 'crypto', 'open', 'high', 'low', 'close',
            'retorno_diario_pct', 'retorno_7d_pct', 'retorno_30d_pct',
            'retorno_acumulado_pct', 'volatilidad_30d',
            'max_52s', 'min_52s', 'anio', 'mes', 'mes_nombre', 'trimestre']
    cols = [c for c in cols if c in df.columns]

    r_hist    = 'data/powerbi/historico_precios.xlsx'
    r_resumen = 'data/powerbi/resumen_cryptos.xlsx'

    for r in [r_hist, r_resumen]:
        if os.path.exists(r):
            print(f'[AVISO] Sobreescribiendo: {r}')

    df[cols].to_excel(r_hist, index=False)
    assert os.path.exists(r_hist), f'ERROR: no se generó {r_hist}'

    df_resumen.to_excel(r_resumen, index=False)
    assert os.path.exists(r_resumen), f'ERROR: no se generó {r_resumen}'

    vol_rows = 0
    if 'volume' in df.columns:
        r_vol = 'data/powerbi/volumen_mensual.xlsx'
        if os.path.exists(r_vol):
            print(f'[AVISO] Sobreescribiendo: {r_vol}')
        vol_mensual = df.groupby(['crypto', 'anio', 'mes', 'mes_nombre']).agg(
            volumen_total=('volume', 'sum'),
            precio_promedio=('close', 'mean')
        ).reset_index()
        vol_mensual.to_excel(r_vol, index=False)
        assert os.path.exists(r_vol), f'ERROR: no se generó {r_vol}'
        vol_rows = len(vol_mensual)

    n_cryptos = df['crypto'].nunique()
    print('\n=== ACCOUNTING ===')
    print(f'Cryptos procesadas  : {n_cryptos} de {len(CRYPTOS)}')
    print(f'Filas históricas    : {len(df[cols]):,}')
    print(f'Filas resumen       : {len(df_resumen):,}')
    print(f'Filas vol. mensual  : {vol_rows:,}')
    print(f'Rango de fechas     : {df["fecha"].min().date()} → {df["fecha"].max().date()}')
    print(f'\n  {r_hist}')
    print(f'  {r_resumen}')
    print('\nEn Power BI: Obtener datos → Excel → seleccionar cada archivo')


if __name__ == '__main__':
    main()
