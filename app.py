from flask import Flask, render_template, url_for, request, redirect, flash, jsonify, session as login_session
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from models import Base, Category, User, Item
from werkzeug import secure_filename
from appForms import DeleteItemForm, EditItemForm, UploadImageForm


__author__ = 'Sotsir'

app = Flask(__name__)

engine = create_engine('sqlite:///item_catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
db_session = DBSession()


@app.route('/')
def index():
    categories = db_session.query(Category).order_by(Category.name).all()
    latest_items = db_session.query(Item).order_by(desc(Item.modified_date)).limit(15).all()
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


@app.route('/categories/<category_id>/items/<item_id>/delete/', methods=['GET', 'POST'])
def delete_item(category_id, item_id):
    form = DeleteItemForm()
    item = db_session.query(Item).filter_by(id=item_id, category_id=category_id).one()
    if form.validate_on_submit():
        db_session.delete(item)
        db_session.commit()
        flash("Item '{}' successfully deleted".format(item.name))
        return redirect(url_for('index'))
    else:
        categories = db_session.query(Category).order_by(Category.name).all()
        return render_template('delete_item.html', categories=categories, active_category=int(category_id),
                               item=item, form=form, logged_in=False)


@app.route('/categories/<category_id>/items/<item_id>/edit/', methods=['GET', 'POST'])
def edit_item(category_id, item_id):
    item = db_session.query(Item).filter_by(id=item_id, category_id=category_id).one()
    form = EditItemForm(request.form, item)
    if form.validate_on_submit():
        form.populate_obj(item)
        db_session.add(item)
        db_session.commit()
        flash("Item '{}' successfully edited".format(item.name))
        return redirect(url_for('get_item_by_category', category_id=item.category_id, item_id=item_id))
    else:
        categories = db_session.query(Category).order_by(Category.name).all()
        return render_template('edit_item.html', categories=categories, active_category=int(category_id),
                               item=item, form=form, logged_in=False)


@app.route('/json/categories/<category_id>/items/<item_id>/')
def json_api_get_item_by_category(category_id, item_id):
    item = db_session.query(Item).filter_by(id=item_id, category_id=category_id).one()
    return jsonify(item.serialize)


@app.route('/items/<item_id>/upload/', methods=['GET', 'POST'])
def image_upload(item_id):
    form = UploadImageForm()
    item = db_session.query(Item).filter_by(id=item_id).one()
    categories = db_session.query(Category).order_by(Category.name).all()
    if form.validate_on_submit():
        filename = 'images/' + secure_filename(form.photo.data.filename)
        form.photo.data.save('static/' + filename)
        item.image_path = filename
        db_session.add(item)
        db_session.commit()
        flash("Image for '{}' successfully uploaded".format(item.name))
        return redirect(url_for('edit_item', category_id=item.category_id, item_id=item_id))
    return render_template('upload.html', categories=categories, active_category=int(item.category_id),
                           form=form, item=item, logged_in=False)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key_for_catalog_item'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
