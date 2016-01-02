import os
import shutil
from flask import Flask, render_template, url_for, request,\
    redirect, flash, jsonify, session as login_session, make_response
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from models import Base, Category, User, Item
from werkzeug.utils import secure_filename
from appForms import DeleteForm, ItemForm, CategoryForm
from xml.etree.ElementTree import Element, SubElement, tostring
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import random
import string
import httplib2
import json
import requests


__author__ = 'Sotsir'

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secret.json', 'r').read())['web']['client_id']
engine = create_engine('sqlite:///item_catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
db_session = DBSession()


def ensure_dir(file_name):
    dir_name = os.path.dirname(file_name)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def delete_dir(dir_name):
    if os.path.exists(dir_name):
        shutil.rmtree(dir_name)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    print("first")
    try:
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        print('1.1')
        oauth_flow.redirect_uri = 'postmessage'
        print('1.2')
        credentials = oauth_flow.step2_exchange(code.decode('utf-8'))
        print('1.3')
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print("second")
    print("2.1")
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}'.format(credentials.access_token))
    h = httplib2.Http()
    print("2.2")
    print(h.request(url, 'GET')[1])
    result = json.loads(h.request(url, 'GET')[1].decode('utf-8'))
    print("2.3")
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 505)
        response.headers['Content-Type'] = 'application/json'
        return response
    print("third")
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user id does not match given user "), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print("forth")
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client id does not match"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print("fifth")

    # Check to see if user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps("Current user is already connected."), 200)
        response.headers['Content-Type'] = 'application/json'
    # Store the access tokens in the session for later use

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    print('answer: {}'.format(answer.text))
    data = json.loads(answer.text)
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = get_user_id(login_session['email'])
    if not user_id:
        user_id = create_user()
    login_session['user_id'] = user_id
    flash("You are now logged in as %s" % login_session['username'])

    return "success"


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'].encode('utf-8'))
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print(url)
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        flash("Successfully disconnected.")
        return redirect(url_for('index'))
    else:
        flash("Failed to revoke token for given user", "error")
        return redirect(url_for('index'))


@app.route('/')
def index():
    categories = db_session.query(Category).order_by(Category.name).all()
    latest_items = db_session.query(Item).order_by(desc(Item.modified_date)).limit(25).all()

    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state

    return render_template('index.html', categories=categories, items=latest_items,
                           active_category=0, logged_in=('username' in login_session), STATE=state, CLIENT_ID=CLIENT_ID)


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
    form = DeleteForm()
    item = db_session.query(Item).filter_by(id=item_id, category_id=category_id).one()
    if form.validate_on_submit():
        delete_dir('static/images/uploads/' + str(item.id))
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
    form = ItemForm()
    if form.validate_on_submit():
        form.populate_obj(item)
        if len(secure_filename(form.photo.data.filename)) > 0:
            filename = 'images/uploads/' + str(item.id) + '/' + secure_filename(form.photo.data.filename)
            ensure_dir('static/' + filename)
            form.photo.data.save('static/' + filename)
            item.image_path = filename
        db_session.add(item)
        db_session.commit()
        flash("Item '{}' successfully edited".format(item.name))
        return redirect(url_for('get_item_by_category', category_id=item.category_id, item_id=item_id))
    else:
        categories = db_session.query(Category).order_by(Category.name).all()
        return render_template('edit_item.html', categories=categories, active_category=int(category_id),
                               item=item, form=form, logged_in=False)


@app.route('/categories/<category_id>/items/new/', methods=['GET', 'POST'])
def new_item(category_id):
    form = ItemForm()
    item = Item()
    item.name = "New item"
    if form.validate_on_submit():
        form.populate_obj(item)
        db_session.add(item)
        if len(secure_filename(form.photo.data.filename)) > 0:
            db_session.flush()
            filename = 'images/uploads/' + str(item.id) + '/' + secure_filename(form.photo.data.filename)
            ensure_dir('static/' + filename)
            form.photo.data.save('static/' + filename)
            item.image_path = filename
            db_session.add(item)
        db_session.commit()
        flash("Item '{}' successfully added".format(item.name))
        return redirect(url_for('get_item_by_category', category_id=item.category_id, item_id=item.id))
    else:
        categories = db_session.query(Category).order_by(Category.name).all()
        return render_template('new_item.html', categories=categories, active_category=int(category_id),
                               item=item, form=form, logged_in=False)


@app.route('/categories/new/', methods=['GET', 'POST'])
def new_category():
    form = CategoryForm()
    category = Category()
    category.name = "New item"
    if form.validate_on_submit():
        form.populate_obj(category)
        db_session.add(category)
        db_session.commit()
        flash("Category '{}' successfully added".format(category.name))
        return redirect(url_for('get_category', category_id=category.id))
    else:
        categories = db_session.query(Category).order_by(Category.name).all()
        return render_template('new_category.html', categories=categories,
                               active_category=-1,
                               form=form, logged_in=False)


@app.route('/categories/<category_id>/edit/', methods=['GET', 'POST'])
def edit_category(category_id):
    category = db_session.query(Category).filter_by(id=category_id).one()
    form = CategoryForm(request.form, category)
    if form.validate_on_submit():
        form.populate_obj(category)
        db_session.add(category)
        db_session.commit()
        flash("Category '{}' successfully updated".format(category.name))
        return redirect(url_for('get_category', category_id=category.id))
    else:
        categories = db_session.query(Category).order_by(Category.name).all()
        return render_template('edit_category.html', categories=categories,
                               active_category=category_id,
                               form=form, logged_in=False)


@app.route('/categories/<category_id>/delete/', methods=['GET', 'POST'])
def delete_category(category_id):
    category = db_session.query(Category).filter_by(id=category_id).one()
    form = DeleteForm()
    if form.validate_on_submit():
        items = db_session.query(Item).filter_by(category_id=category_id).all()
        for item in items:
            delete_dir('static/images/uploads/' + str(item.id))
        db_session.delete(category)
        db_session.commit()
        flash("Category '{}' successfully deleted".format(category.name))
        return redirect(url_for('index'))
    else:
        categories = db_session.query(Category).order_by(Category.name).all()
        return render_template('delete_category.html', categories=categories, active_category=int(category_id),
                               category=category, form=form, logged_in=False)


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


@app.route('/json/categories/<category_id>/items/<item_id>/')
def json_api_get_item_by_category(category_id, item_id):
    item = db_session.query(Item).filter_by(id=item_id, category_id=category_id).one()
    return jsonify(item.serialize)


@app.route('/xml/categories/')
def xml_api_categories():
    categories = db_session.query(Category).order_by(Category.name).all()
    data = Element('categories')
    for category in categories:
        cat_id = SubElement(data, 'id')
        cat_id.text = str(category.id)
        cat_name = SubElement(data, 'name')
        cat_name.text = category.name
        items = SubElement(data, 'items')
        for item in category.items:
            item_id = SubElement(items, 'id')
            item_id.text = str(item.id)
            item_name = SubElement(items, 'name')
            item_name.text = item.name
            item_description = SubElement(items, 'description')
            item_description.text = item.description
            item_image = SubElement(items, 'image')
            item_image.text = item.image_path
            item_modified_date = SubElement(items, 'modified_date')
            item_modified_date.text = str(item.modified_date)
    return app.response_class(tostring(data), mimetype='application/xml')


def create_user():
    new_user = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    db_session.add(new_user)
    db_session.commit()
    user = db_session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def get_user_info(user_id):
    user = db_session.query(User).filter_by(id=user_id).one()
    return user


def get_user_id(email):
    try:
        user = db_session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


if __name__ == '__main__':
    app.secret_key = 'super_secret_key_for_catalog_item'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
