from flask import Flask, request, render_template
import time
import yfinance as yf
import pandas as pd
import talib
import openai

openai.api_key = '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'

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def landing():
    return render_template('index.html')


@app.route('/zonemaster', methods=['GET', 'POST'])
def zonemaster():
    return render_template('zonemaster.html')


@app.route('/respuesta', methods=['POST'])
def home():
    if request.method == "POST":
        if 'analizar' in request.form:
            symbol = request.form['ticker']
            time_frame_mayor = request.form['timeFrameMayor']
            time_frame_menor = request.form['timeFrameMenor']
            answer = interaccion(symbol, time_frame_mayor, time_frame_menor)

    return render_template('zonemaster.html', answer=answer)


def interaccion(symbol, time_frame_mayor, time_frame_menor):
    cant = 0
    openai.api_key = ''
    messages = []
    messages.append({"role": "system",
                     "content": """Actua como el mejor analista tecnico de trading y utilizando los datos que te proporcione de Fecha, apertura, alto, low, close, volumen, SMA de 20, SMA de 200, EMA 50, RSI, MACD, Estocastico, OBV y CCI, puedas identificar las zonas de demanda y oferta segun los datos yo te enviare estos datos en tiempo real y solo tendras que analizar la informacion como analista tecnico y utilizando accion del precio y con esa información solo me responderas con las zonas de precio de posibles compras y zonas de precios de posibles ventas con solo 20 palabras"""})

    ma_period = 21
    ema_period = 50
    ma_period_lenta = 200
    rsi_period = 14
    while cant < 2:
        cant += 1
        # Crear un objeto Ticker con el símbolo de la acción
        ticker = yf.Ticker(symbol)

        if cant == 1:
            periodo = "1y"
            intervalo = time_frame_mayor

        elif cant == 2:
            periodo = "59d"
            intervalo = time_frame_menor

            # Obtener los datos históricos de la acción en temporalidad de horas
        data = pd.DataFrame(ticker.history(period=periodo, interval=intervalo))  # 1 mes, intervalo de 5 minutos

        # Eliminar las columnas "Dividends" y "Stock Splits"
        if 'Dividends' in data.columns and 'Stock Splits' in data.columns:
            # Eliminar las columnas
            data = data.drop(['Dividends', 'Stock Splits'], axis=1)

        try:
            # Calcular la media móvil simple de 21 períodos
            data['MA21'] = talib.SMA(data['Close'], ma_period)
        except Exception as e:
            data['MA21'] = e

        try:
            # Calcular la media móvil exponencial de 50 períodos
            data['EMA50'] = talib.EMA(data['Close'], ema_period)
        except Exception as e:
            data['EMA50'] = e

        try:
            # Calcular la media móvil simple de 200 períodos
            data['MA200'] = talib.SMA(data['Close'], ma_period_lenta)
        except Exception as e:
            data['MA200'] = e

        try:
            # Calcular el RSI
            data['RSI'] = talib.RSI(data['Close'], rsi_period)
        except Exception as e:
            data['RSI'] = e

        try:
            # Calcular el MACD y su línea de señal utilizando los precios de cierre
            data['MACD'], signal, _ = talib.MACD(data["Close"])
        except Exception as e:
            data['MACD'] = e

        try:
            # Imprimir los valores del Stoch y su línea de señal
            data['STOCH'], lento = talib.STOCH(data["High"], data["Low"], data["Close"])
        except Exception as e:
            data['STOCH'] = e

        try:
            # Calcular el OBV
            data['OBV'] = talib.OBV(data["Close"], data["Volume"])
        except Exception as e:
            data['OBV'] = e

        try:
            # Calcular el CCI
            data['CCI'] = talib.CCI(data["High"], data["Low"], data["Close"])
        except Exception as e:
            data['CCI'] = e

        data_ok = data.tail(10)
        df_json = data_ok.to_json()

        def chat_ia(prompt):
            question = {}
            response_ia = {}
            question['role'] = 'user'
            question['content'] = prompt
            messages.append(question)

            try:
                response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)

                try:
                    answer = response['choices'][0]['message']['content']
                    response_ia['role'] = 'assistant'
                    response_ia['content'] = answer
                    messages.append(response_ia)

                except:
                    answer = 'Hemos tenido un error al recibir la respuesta de openai'
            except Exception as e:
                answer = f'Hay un error {e}, para soporte contactar con https://t.me/jetrader_cu'

            return answer

        if cant == 1:
            respuesta_primera = chat_ia(df_json)
        elif cant == 2:
            respuesta_segunda = chat_ia(df_json)
    time.sleep(2)
    respuesta = f'Esta son las zonas para el timeframe mayor:\n\n{respuesta_primera}\n\n\nEsta son las zonas para el timeframe menor:\n\n{respuesta_segunda}'
    return respuesta


if __name__ == '__main__':
    app.run()
