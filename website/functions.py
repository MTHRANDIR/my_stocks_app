from datetime import datetime, timedelta
import investpy as ip
import pandas as pd
import pandas_datareader.data as web
import json
import plotly
import plotly.graph_objs as go
import plotly.express as px
import requests
from bs4 import BeautifulSoup
import riskfolio as rp
import numpy as np
from scipy.optimize import minimize


def stock_value(ticker, country, date=None):
    if date == None or date == datetime.now().strftime('%d/%m/%Y'):  # assume que é no dia de hoje
        # shareValue =          criar condicional para horario, se aberto valor atual beaultiful soup, se fechado valor do fechamento do dia anterior
        shareValue = str(ip.stocks.get_stock_information(
            stock=ticker, country=country)['Open']).split()[1]
    else:
        shareValue = ip.get_stock_historical_data(stock=ticker, country=country, from_date=date, to_date=datetime.now(
        ).strftime('%d/%m/%Y'), interval='Daily')['Close'][0]

    return shareValue


def plot_portifolio_performance(portifolio):
    return 1


def stock_historical_data_plotStick(stock, country, from_date, to_date, interval):
    df = ip.get_stock_historical_data(stock=stock,
                                      # ['brazil','united states']
                                      country=country,
                                      from_date=from_date.strftime('%d/%m/%Y'),
                                      to_date=to_date.strftime('%d/%m/%Y'),
                                      interval=interval)  # ['Daily', 'Weekly', 'Monthly']
    trace1 = {
        'x': df.index,
        'open': df.Open,
        'close': df.Close,
        'high': df.High,
        'low': df.Low,
        'type': 'candlestick',
        'name': stock,
        'showlegend': False
    }
    data = [trace1]
    layout = go.Layout()
    fig = go.Figure(data=data, layout=layout)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


def stock_value_live(ticker, country):

    url = requests.get(assemble_site(ticker, country))
    page = url.text
    soup = BeautifulSoup(page, "html.parser")
    dados = soup.find_all('div', attrs={'class': 'kf1m0'})

    try:
        value = dados[0].get_text().split()[1]
        shareValue = float(value.replace('.', '').replace(',', '.'))
    except:
        ####################################################
        print('close value, from last day ')
        ####################################################
        shareValue = stock_value(ticker, country)
    return shareValue


def assemble_site(ticker, country):
    if country == 'united states':
        return "https://www.google.com/finance/quote/"+ticker+":NASDAQ?hl=pt"
    else:
        return "https://www.google.com/finance/quote/"+ticker+":BVMF?hl=pt"


def portfolio_value_live(portfolio_Stocks):
    value = 0.0
    for Stock in portfolio_Stocks:
        value = value + \
            stock_value_live(Stock.ticker, Stock.country)*Stock.shares

    return value


def portfolio_weights(portfolio_Stocks):
    total = portfolio_value_live(portfolio_Stocks)
    w = []
    for Stock in portfolio_Stocks:
        w.append(stock_value_live(Stock.ticker,
                                  Stock.country)*Stock.shares/total)
    return w


def portfolio_expected_return(portfolio, from_date, to_date, interval='Daily'):

    # possible error: first stock is from US and the others from brazil
    if portfolio.stocks[0].country == 'united states':
        stocks_ticker = [stock.ticker for stock in portfolio.stocks]
        stoks_df = web.DataReader(
            stocks_ticker, 'yahoo', from_date.strftime('%Y/%m/%d'), to_date.strftime('%Y/%m/%d'))['Close']
        stoks_df.columns = portfolio.stocks
        Y = stoks_df[portfolio.stocks].pct_change().dropna()

    else:
        data = ip.get_stock_historical_data(stock=portfolio.stocks[0].ticker,
                                            country='brazil',
                                            from_date=from_date.strftime(
                                                '%d/%m/%Y'),
                                            to_date=to_date.strftime(
                                                '%d/%m/%Y'),
                                            interval=interval)['Close']
        for stock in portfolio.stocks[1:]:
            df = ip.get_stock_historical_data(stock=stock.ticker,
                                              country=stock.country,
                                              from_date=from_date.strftime(
                                                  '%d/%m/%Y'),
                                              to_date=to_date.strftime(
                                                  '%d/%m/%Y'),
                                              interval=interval)['Close']
            data = pd.concat([data, df], axis=1)
        data.columns = portfolio.stocks
        Y = data[portfolio.stocks].pct_change().dropna()

    return Y


def portfolio_return(returns, w):
    return np.sum(returns.mean()*w)


def portfolio_covar(returns):
    return rp.covar_matrix(returns)


def portfolio_risk(w, cov, returns):
    return rp.RiskFunctions.Sharpe_Risk(w, cov=cov, returns=returns, rm='MV', rf=0, alpha=0.05, a_sim=100, beta=None, b_sim=None)


def checkSumToOne(w):
    return np.sum(w)-1


def optimize_portfolio_heights(Stocks, cov, returns):
    # adicionar parametros risco return .....
    w0 = [1/len(Stocks) for i in range(len(Stocks))]
    bounds = tuple([(0, 1) for i in range(len(Stocks))])
    constraints = ({'type': 'eq', 'fun': checkSumToOne})
    # lambda f or portfolio_risk
    w_opt = minimize(lambda w: rp.RiskFunctions.Sharpe_Risk(w, cov=cov, returns=returns, rm='MV', rf=0, alpha=0.05, a_sim=100, beta=None, b_sim=None), w0, method='SLSQP',
                     bounds=bounds, constraints=constraints)

    return w_opt.x


def portifolio_historical_data_compare(portfolio, from_date, to_date, interval, w_optimized=[None]):

    df = ip.get_stock_historical_data(stock=portfolio.stocks[0].ticker,
                                      # ['brazil','united states']
                                      country=portfolio.stocks[0].country,
                                      from_date=from_date.strftime('%d/%m/%Y'),
                                      to_date=to_date.strftime('%d/%m/%Y'),
                                      interval=interval)['Close']  # ['Daily', 'Weekly', 'Monthly']
    df.columns = [portfolio.stocks[0].ticker]
    data = df*portfolio.stocks[0].shares
    if w_optimized[0] != None:
        data_opt = df
    for Stock in portfolio.stocks[1:]:
        df = ip.get_stock_historical_data(stock=Stock.ticker,
                                          # ['brazil','united states']
                                          country=Stock.country,
                                          from_date=from_date.strftime(
                                              '%d/%m/%Y'),
                                          to_date=to_date.strftime('%d/%m/%Y'),
                                          interval=interval)['Close']  # ['Daily', 'Weekly', 'Monthly']
        df.columns = [Stock.ticker]
        data = data + df*Stock.shares

        if w_optimized[0] != None:
            data_opt = pd.concat([data_opt, df], axis=1)

    bova11 = ip.get_etf_historical_data('Ishares Ibovespa',
                                        country=Stock.country,
                                        from_date=from_date.strftime(
                                            '%d/%m/%Y'),
                                        to_date=to_date.strftime('%d/%m/%Y'),
                                        interval=interval)['Close']
    normalize = (bova11/bova11[0])*data[0]
    data = pd.concat([data, normalize], axis=1)
    data.columns = ['my_portifolio', 'bova11']
    data_opt.describe()
    if w_optimized[0] != None:
        totalPrice = data['my_portifolio'][0]
        optimized_portfolio = data_opt.iloc[:, 0] * \
            totalPrice*w_optimized[0]/data_opt.iloc[0, 0]
        i = 1
        for i in range(1, len(data_opt.iloc[0, :])):
            optimized_portfolio = optimized_portfolio + \
                (data_opt.iloc[:, i]*totalPrice *
                 w_optimized[i])/data_opt.iloc[0, i]

        data = pd.concat([data, optimized_portfolio], axis=1)
        data.columns = ['my_portifolio', 'bova11', 'optimized_portfolio']

    fig = px.line(data, y=data.columns)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON
