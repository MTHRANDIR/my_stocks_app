from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from flask_wtf import FlaskForm
from wtforms import SelectField


class Form(FlaskForm):
    country = SelectField('country', choices=['Brazil', 'united states'])


class Stock_list(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10))
    country = db.Column(db.String(50))


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    notes = db.relationship('Note')
    portfolio = db.relationship('Portfolio')
    selected_portifolio = db.Column(db.Integer)


class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True)
    stocks = db.relationship('Stock')
    profit = db.Column(db.Integer)
    invested = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10))
    country = db.Column(db.String(30))
    shares = db.Column(db.Integer)
    profit = db.Column(db.Float)
    invested = db.Column(db.Float)
    buy_date = db.Column(db.DateTime(timezone=True), default=func.now())
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'))


class Sell_stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10))
    country = db.Column(db.String(30))
    shares = db.Column(db.Integer)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    price = db.Column(db.Float)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'))
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'))


class Buy_stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10))
    country = db.Column(db.String(30))
    shares = db.Column(db.Integer)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    price = db.Column(db.Float)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'))
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'))
