from flask import Flask, render_template, url_for, request, redirect, flash, jsonify, session as login_session
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from models import Base, Category, User, Item

__author__ = 'Sotsir'

app = Flask(__name__)

engine = create_engine('sqlite:///item_catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
db_session = DBSession()


@app.route('/')
def index():
    categories = db_session.query(Category).order_by(Category.name).all()
    return render_template('index.html', categories=categories, active_category=0, logged_in=False)


@app.route('/categories/<category_id>/')
def get_category(category_id):
    categories = db_session.query(Category).order_by(Category.name).all()
    category = db_session.query(Category).filter_by(id=category_id).one()
    return render_template('items.html', categories=categories, active_category=int(category_id), logged_in=False)


@app.route('/categories/json/')
def categories_json():
    categories = db_session.query(Category).order_by(Category.name).all()
    return jsonify(categories=[r.serialize for r in categories])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key_for_catalog_item'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
