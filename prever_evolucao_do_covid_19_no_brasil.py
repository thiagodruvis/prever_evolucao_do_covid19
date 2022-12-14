# -*- coding: utf-8 -*-
"""Prever_Evolucao_do_COVID-19_no_Brasil.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1o5cMP_oPi4B7FQ6vmot-9S2HOteprUkM

# Projeto COVID-19

## Digital Innovation One

Primeiro vamos importar algumas das biblio necessárias para nosso projeto de hoje.
"""

import pandas as pd 
import numpy as np 
from datetime import datetime 
import plotly.express as px 
import plotly.graph_objects as go

# vamos importar os dados para o projeto 
url = 'https://raw.githubusercontent.com/neylsoncrepalde/projeto_eda_covid/master/covid_19_data.csv'

df = pd.read_csv(url, parse_dates=['ObservationDate', 'Last Update'])
df

# Conferindo os tipos de cada coluna 
df.dtypes

"""Matendo o padrão de boas práticas, os nomes de colunas não devem ter letras maísculas e nem caracteres especiais. Vamos implementar uma função para fazer a limpeza dos nomes dessas colunas """

# importando o re para fazer uma função regular 
import re

def corrige_colunas(col_name):
    return re.sub(r"[/| ]", "", col_name).lower()

corrige_colunas("AdgE/P ou") # pegando uma amostra de ex para testra a função

# Corrigindo todas as colunas do df 
df.columns = [corrige_colunas(col) for col in df.columns]

df #para checar se as colunas foram alteradas da maneira correta

"""# Brasil 

Vamos pegar o scopo do Brasil para investigar
"""

# para visualizar todos os países que fazem parte do df

df.countryregion.unique()

df.loc[df.countryregion == 'Brazil']

brasil = df.loc[
    (df.countryregion == 'Brazil') &
    (df.confirmed > 0)
]

brasil #chama o objeto pra conferir a aplicação do filtro

"""## Casos confimados"""

# Gráfico da evolução de casos confirmados 
px.line(brasil, 'observationdate', 'confirmed', title = 'Casos Confirmados no Brasil')

"""# Descobrindo novos casos por dia """

brasil.shape[0]

# Técnica de programação funcional  #criar uma nova coluna 'novos casos' 
# programando uma função anonima (lambda) 
# .iloc[x] faz o subset pelo índice  

brasil['novoscasos'] = list(map(
    lambda x: 0 if (x==0) else brasil['confirmed'].iloc[x] - brasil['confirmed'].iloc[x-1],
    np.arange(brasil.shape[0])
))

brasil #checando a criação da nova coluna

# vizualizando os novos cavos em um gráfico 
px.line(brasil, x='observationdate', y='novoscasos', title='Novos casos por dia')

"""# Mortes"""

# o trace é uma camada de dados # o comando do Scatterplot para obter linhas e colunas  

fig = go.Figure()

fig.add_trace(
    go.Scatter(x=brasil.observationdate, y=brasil.deaths, name='Mortes',   
              mode='lines+markers', line={'color':'red'})
)

# layout
fig.update_layout(title='Mortes por COVID-19 no Brasil')

fig.show()

"""# Taxa de Crescimento """

# taxa_crescimento = (presente/passado)**(1/n)-1 prever a taxa média de crescimento por todo periodo avaliado
   # se data início for None, define como a primeira data disponível 
def taxa_crescimento(data, variable, data_inicio=None, data_fim=None):
    if data_inicio == None: 
        data_inicio = data.observationdate.loc[data[variable] > 0].min()
    else: 
        data_inicio = pd.to_datetime(data_inicio)
        
    if data_fim == None:
        data_fim = data.observationdate.iloc[-1]
    else:
        data_fim = pd.to_datetime(data_fim)
        
    #Define os valores do presente e passado 
    passado = data.loc[data.observationdate == data_inicio, variable].values[0]
    presente = data.loc[data.observationdate == data_fim, variable].values[0]
    
    # Define o número de pontos no tempo que vamos avaliar 
    n = (data_fim - data_inicio).days 
    
    # Calcular a taxa
    taxa = (presente/passado)**(1/n) - 1 
    
    return taxa*100

# taxa de crescimento médio do COVID no Brasil em todo período 
taxa_crescimento(brasil, 'confirmed')

from numpy.core.fromnumeric import var
# defindo taxa de crescimento diário de casos de covid 
def taxa_crescimento_diario(data, variable, data_inicio=None):
  # se data incio for None, define como a primeira disponível 
  if data_inicio == None: 
        data_inicio = data.observationdate.loc[data[variable] > 0].min()
  else: 
      data_inicio = pd.to_datetime(data_inicio)
  
  data_fim = data.observationdate.max()
  # Define o numero de pontos no tempo que vamos avaliar
  n = (data_fim - data_inicio).days

  # Taxa calculada de um para o outro 
  taxas = list(map(
      lambda x: (data[variable].iloc[x] - data[variable].iloc[x-1]) / data[variable].iloc[x-1],
      range(1, n+1)
  ))
  return np.array(taxas)*100

tx_dia = taxa_crescimento_diario(brasil, 'confirmed')

tx_dia

primeiro_dia = brasil.observationdate.loc[brasil.confirmed > 0].min()

px.line(x=pd.date_range(primeiro_dia, brasil.observationdate.max())[1:],
        y=tx_dia, title='Taxa de crescimento de casos confirmados no Brasil')

"""# Predições"""

# importar duas bibliotecas novas 
from statsmodels.tsa.seasonal import seasonal_decompose
import matplotlib.pyplot as plt

casos_confirmados = brasil.confirmed
casos_confirmados.index = brasil.observationdate
casos_confirmados

# Fazer a decomposição dos casos confirmados
res = seasonal_decompose(casos_confirmados)

# precisamos de 4 itens os observados, tendêcia, sazonalidade e o ruído
fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(10,8))

ax1.plot(res.observed)
ax2.plot(res.trend)
ax3.plot(res.seasonal)
ax4.plot(casos_confirmados.index, res.resid)
ax4.axhline(0, linestyle='dashed', c='black')
plt.show()

"""# **ARIMA**"""

#instalando o pacote 
!pip install pmdarima

from pmdarima.arima import auto_arima
modelo = auto_arima(casos_confirmados)

fig = go.Figure(go.Scatter(
    x=casos_confirmados.index, y=casos_confirmados, name='Observados'
))

fig.add_trace(go.Scatter(
    x=casos_confirmados.index, y=modelo.predict_in_sample(), name='Preditos'
))

fig.add_trace(go.Scatter(
    x=pd.date_range('2020-05-20', '2020-06-20'), y=modelo.predict(31), name='Forecast'
))

fig.update_layout(title='Previsão de casos confirmados no Brasil para os próximos 30 dias')
fig.show()

"""# Modelo de crescimento 

vamos usar a biblioteca fbpophet 
"""

!conda install -c conda-forge fbprophet -y

from fbprophet import Prophet

# preprocessamentos 

train = casos_confirmados.reset_index()[:-5]
test = casos_confirmados.reset_index()[-5:]

# Renomeando colunas
train.rename(columns={'observationdate':'ds', 'confirmed': 'y'}, inplace=True)
test.rename(columns={'observationdate':'ds', 'confirmed' : 'y'}, inplace=True)

# Definir o modelo de crescimento 
profeta = Prophet(growth='logistic', changepoints=['2020-03-21', '2020-03-30', '2020-04-25',
                                                   '2020-05-03', '2020-05-10'])
#pop = 2114463256
pop = 1000000
train['cap'] = pop

# treina o modelo
profeta.fit(train)

# construir previsões para o futuro 
future_dates = profeta.make_future_dataframe(periods=200)
future_dates['cap'] = pop
forecast = profeta.predict(future_dates)

fig = go.figure()

fig.add_trace(go.Scatter(x=forecast.ds, y=forecast.yhat,name='Predição'))
fig.add_trace(go.Scatter(x=train.ds, y=train.y ,name='Observados - Treino'))
fig.update_layout(title='Predições de casos confirmados no Brasil')
fig.show()