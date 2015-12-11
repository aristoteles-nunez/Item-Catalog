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
    latest_items = db_session.query(Item).order_by(desc(Item.modified_date)).all()
    return render_template('index.html', categories=categories, items=latest_items,
                           active_category=0, logged_in=False)


@app.route('/json/categories/')
def json_api_categories():
    categories = db_session.query(Category).order_by(Category.name).all()
    return jsonify(categories=[r.serialize for r in categories])


@app.route('/json/items/')
def json_api_items():
    items = db_session.query(Item).order_by(desc(Item.modified_date)).all()
    return jsonify(items=[r.serialize for r in items])


@app.route('/json/items/<item_id>/')
def json_api_get_item(item_id):
    item = db_session.query(Item).filter_by(id=item_id).one()
    return jsonify(item.serialize)


@app.route('/categories/<category_id>/items/')
def get_category(category_id):
    categories = db_session.query(Category).order_by(Category.name).all()
    items = db_session.query(Item).filter_by(category_id=category_id).order_by(Item.name).all()
    return render_template('index.html', categories=categories, active_category=int(category_id),
                           items=items, logged_in=False)


@app.route('/json/categories/<category_id>/items/')
def json_api_get_category(category_id):
    items = db_session.query(Item).filter_by(category_id=category_id).order_by(Item.name).all()
    return jsonify(items=[r.serialize for r in items])


@app.route('/categories/<category_id>/items/<item_id>/')
def get_item_by_category(category_id, item_id):
    categories = db_session.query(Category).order_by(Category.name).all()
    item = db_session.query(Item).filter_by(id=item_id, category_id=category_id).one()
    return render_template('items.html', categories=categories, active_category=int(category_id),
                           item=item, logged_in=False)


@app.route('/json/categories/<category_id>/items/<item_id>/')
def json_api_get_item_by_category(category_id, item_id):
    item = db_session.query(Item).filter_by(id=item_id, category_id=category_id).one()
    return jsonify(item.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key_for_catalog_item'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
