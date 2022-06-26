from flask import Blueprint, render_template, request, flash, jsonify, Flask
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from flask_wtf import FlaskForm
from wtforms import SelectField
from .models import Note, User

from . import db
import json
from .models import Stock, Portfolio, Sell_stock, Buy_stock, Form
from .functions import stock_value, stock_historical_data_plotStick, portifolio_historical_data_compare, optimize_portfolio_heights, portfolio_covar, portfolio_risk, portfolio_expected_return, portfolio_return, portfolio_weights, portfolio_value_live


views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():

    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)


@views.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})


@views.route('/delete-portfolio', methods=['POST'])
def delete_portfolio():
    note = json.loads(request.data)
    portfolioId = note['portfolioId']
    portfolio = Portfolio.query.get(portfolioId)
    if portfolio:
        if portfolio.user_id == current_user.id:
            db.session.delete(portfolio)
            db.session.commit()

    return jsonify({})


@login_required
@views.route('/create_portfolio', methods=['GET', 'POST'])
def add_stock():
    if request.method == 'POST':
        portfolio_name = request.form.get('name')
        if portfolio_name == None or portfolio_name == '':
            portfolio_name = request.form.get('portfolio2')
            print("portfolio_name")
            print(portfolio_name)

        if len(portfolio_name) < 1:
            flash('Portfolio name is too short!', category='error')
        else:
            portfolio = Portfolio.query.filter_by(name=portfolio_name).first()
            if portfolio:
                flash('Portfolio selected', category='success')
            else:
                new_portfolio = Portfolio(
                    name=portfolio_name, user_id=current_user.id, invested=0, profit=0)
                db.session.add(new_portfolio)
                db.session.commit()
                flash('New portfolio created!', category='success')

            ticker = request.form.get('ticker')
            country = request.form.get('country')
            shares = request.form.get('shares')
            price = request.form.get('price')
            portfolio = Portfolio.query.filter_by(name=portfolio_name).first()
            stock = Stock.query.filter_by(
                portfolio_id=portfolio.id).filter_by(ticker=ticker).first()
            date = request.form.get('date')

            if date == None or date == '':
                date = datetime.now()

            else:
                date = datetime.strptime(date, '%Y-%m-%d')

            if price == None or price == '':
                price = stock_value(
                    ticker, country, datetime.strftime(date, '%d/%m/%Y'))

            price_float = float(price)
            shares_float = float(shares)

            if stock:
                flash('stock allredy exist in the portfolio : ' +
                      str(portfolio.name), category='success')
                if int(shares) < 0:
                    # sell operation
                    if -int(shares) > int(stock.shares):
                        flash('you dont have that many shares to sell!',
                              category='error')
                        return render_template("create_portfolio.html", user=current_user)
                    else:
                        profit = - price_float * shares_float
                        if stock.profit == None or stock.profit == '':
                            old = 0
                        else:
                            old = float(stock.profit)
                        Stock.query.filter_by(portfolio_id=portfolio.id).filter_by(ticker=ticker).update(
                            {'shares': int(stock.shares)+int(shares), 'profit': old+profit})
                        db.session.commit()
                        Portfolio.query.filter_by(id=portfolio.id).update(
                            {'profit': portfolio.profit+profit})
                        db.session.commit()
                        new_sell = Sell_stock(ticker=ticker, country=country, shares=shares,
                                              portfolio_id=portfolio.id, stock_id=stock.id, price=float(price), date=date)
                        db.session.add(new_sell)
                        db.session.commit()
                        flash('sell operation complete : ', category='success')

                else:
                    invested = price_float * shares_float

                    Stock.query.filter_by(portfolio_id=portfolio.id).filter_by(ticker=ticker).update(
                        {'shares': int(stock.shares) + int(shares), 'invested': float(stock.invested)+invested})
                    db.session.commit()
                    Portfolio.query.filter_by(id=portfolio.id).update(
                        {'invested': portfolio.invested + invested})
                    db.session.commit()
                    new_buy = Buy_stock(ticker=ticker, country=country, shares=shares, date=date, price=float(
                        price), stock_id=stock.id, portfolio_id=portfolio.id)
                    db.session.add(new_buy)
                    db.session.commit()
                    flash('buy operation complete : ', category='success')
                    # buy operation

            else:
                if int(shares) < 1:
                    flash('number of shares must be positive', category='error')
                else:
                    invested = price_float * shares_float
                    new_stock = Stock(ticker=ticker, country=country, shares=shares,
                                      portfolio_id=portfolio.id, invested=invested, profit=0)
                    db.session.add(new_stock)
                    db.session.commit()
                    stock = Stock.query.filter_by(
                        portfolio_id=portfolio.id).filter_by(ticker=ticker).first()
                    new_buy = Buy_stock(ticker=ticker, country=country, shares=shares,
                                        date=date, price=price, stock_id=stock.id, portfolio_id=portfolio.id)
                    db.session.add(new_buy)
                    db.session.commit()
                    Portfolio.query.filter_by(id=portfolio.id).update(
                        {'invested': portfolio.invested + invested})
                    db.session.commit()

                    flash('new stock added!', category='success')
        atual = current_user.portfolio.index(portfolio)
        User.query.filter_by(id=current_user.id).update(
            {'selected_portifolio': atual})

    return render_template("create_portfolio.html", user=current_user)


@login_required
@views.route('/Stock_view', methods=['GET', 'POST'])
def plot_stock():
    if request.method == 'POST':
        stock = request.form.get('select_stock')
        country = request.form.get('select_country')
        interval = request.form.get('select_interval')
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')

        if to_date:
            to_date2 = datetime.strptime(to_date, '%Y-%m-%d')
        else:
            to_date2 = datetime.today()

        if from_date:
            from_date2 = datetime.strptime(from_date, '%Y-%m-%d')
        else:
            from_date2 = datetime.today() - timedelta(days=60)

        graphJSON = stock_historical_data_plotStick(
            stock, country, from_date2, to_date2, interval)
        # print(graphJSON)
        # print("graphJSON")
        return render_template("Stock_view.html", user=current_user, graphJSON=graphJSON)

    return render_template("Stock_view.html", user=current_user)


@login_required
@views.route('/portfolio_performance', methods=['GET', 'POST'])
def plot_portifolio():
    total_value = 0
    if request.method == 'POST':
        portfolio_name = request.form.get('select_portifolio3')
        interval = request.form.get('select_interval')
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        portfolio = Portfolio.query.filter_by(name=portfolio_name).first()

        if to_date:
            to_date2 = datetime.strptime(to_date, '%Y-%m-%d')
        else:
            to_date2 = datetime.today()

        if from_date:
            from_date2 = datetime.strptime(from_date, '%Y-%m-%d')
        else:
            from_date2 = datetime.today() - timedelta(days=60)

        invested = portfolio.invested
        profit = portfolio.profit
        for stock in portfolio.stocks:
            total_value = total_value + \
                float(stock_value(stock.ticker, stock.country))
        total_value = portfolio_value_live(portfolio.stocks)
        present_Portfolio_value = total_value
        print(total_value)
        total_profit = profit + total_value - invested
        data = {'present_Portfolio_value': present_Portfolio_value,
                'total_profit': total_profit}

        weights = portfolio_weights(portfolio.stocks)
        returns = portfolio_expected_return(
            portfolio, from_date2, to_date2, interval=interval)
        global cov
        cov = portfolio_covar(returns)
        risk = portfolio_risk(weights, cov, returns)
        totalReturn = portfolio_return(returns, weights)

        optimalWeights = optimize_portfolio_heights(
            portfolio.stocks, cov, returns)
        optimalRisk = portfolio_risk(optimalWeights, cov, returns)
        optimalReturn = portfolio_return(returns, optimalWeights)

        data['weights'] = weights
        data['risk'] = risk
        data['totalReturn'] = totalReturn
        data['optimalWeights'] = optimalWeights
        data['optimalRisk'] = optimalRisk
        data['optimalReturn'] = optimalReturn

        graphJSON = portifolio_historical_data_compare(
            portfolio, from_date2, to_date2, interval, optimalWeights)

        print(data)

        return render_template("portfolio_performance.html", user=current_user, data=data, graphJSON=graphJSON)

    return render_template("portfolio_performance.html", user=current_user)
