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
engine = create_engine('postgresql+psycopg2:///item_catalog', client_encoding='utf8')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
db_session = DBSession()


def ensure_dir(file_name):
    """ Method that ensure the existence of a directory that contains a file.
        If the directory doesn't exist it will create one.
    Args:
        file_name: Name of the file that specify the path of the directory.
    """
    dir_name = os.path.dirname(file_name)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def delete_dir(dir_name):
    """ Method that deletes a directory only if it exists.
    Args:
        dir_name: Exactly path of the directory.
    """
    if os.path.exists(dir_name):
        shutil.rmtree(dir_name)


@app.route('/gdisconnect')
def gdisconnect():
    """ Route that makes the logout for Google Oauth account.

    The user is disconnected deleting the information from current login_session, and
     making a request to revoke the token emmited by Google Oauth
    """
    if 'access_token' not in login_session:
        flash("Current user not connected.", "error")
        return redirect(url_for('index'))
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    del login_session['access_token']
    del login_session['gplus_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    if result['status'] == '200':
        flash("Successfully disconnected.")
        return redirect(url_for('index'))
    else:
        flash("Failed to revoke token for given user", "error")
        return redirect(url_for('index'))


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """ Route that makes the authentication for Google Oauth account.

    Once the user authorizes the access to the his Google Oauth info,
      it will be stored into the current login_session and if the user
      does not exists it will be created and stored in database.
    """
    if request.args.get('state') != login_session['state']:
        flash("Invalid state parameter", "error")
        return redirect(url_for('index'))
    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code.decode('utf-8'))
    except FlowExchangeError:
        flash("Failed to upgrade the authorization code", "error")
        return redirect(url_for('index'))
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}'.
           format(credentials.access_token))
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1].decode('utf-8'))
    if result.get('error') is not None:
        flash(result.get('error'), "error")
        return redirect(url_for('index'))
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        flash("Token's user id does not match given user", "error")
        return redirect(url_for('index'))
    if result['issued_to'] != CLIENT_ID:
        flash("Token's client id does not match", "error")
        return redirect(url_for('index'))
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        flash("Current user is already connected.", "error")
        return redirect(url_for('index'))
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
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


@app.route('/')
def index():
    """ Route that renders the index page.

    Every time all the categories are obtained as well as the last 25 modified items.
    The categories are sorted by name and  all the modified items are sorted by modified date.
    The login_session will be passed to template to control the rendered elements
     according to access rules.

    Raises:
        Exception. If something goes wrong, it will be display an error page with the proper
         exception message.
    """
    try:
        logged_in = 'username' in login_session
        categories = db_session.query(Category).order_by(Category.name).all()
        latest_items = db_session.query(Item).order_by(desc(Item.modified_date))\
            .limit(25).all()
        return render_template('index.html', categories=categories, items=latest_items,
                               active_category=0, logged_in=logged_in,
                               login_session=login_session)
    except Exception as e:
        output = '''
        <h1>An error has occurred</h1>
        <p>{}</p>
        '''.format(str(e))
        return output


@app.route('/login/')
def login():
    """ Route that renders the login page.

    It will be displaying all the login methods available, but for the moment only Google Oauth
     will be displayed.
    The CLIENT_ID as well as the STATE is passed to template from the server to dynamic render
     on client side.

    Raises:
        If an error occurs the application will redirect to index page and a flash message
        will be displayed with the proper Exception message.
    """
    try:
        logged_in = 'username' in login_session
        if logged_in:
            flash("User already logged", category="info")
            return redirect(url_for('index'))
        categories = db_session.query(Category).order_by(Category.name).all()
        state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
        login_session['state'] = state
        return render_template('login.html', categories=categories,
                               active_category=-1, logged_in=logged_in, STATE=state,
                               CLIENT_ID=CLIENT_ID)
    except Exception as e:
        flash('An error has occurred: {}'.format(str(e)), 'error')
        return redirect(url_for('index'))


@app.route('/categories/<int:category_id>/items/')
def get_category(category_id):
    """ Route that renders the page for a specific category with the contained items.

    All the contained items are sorted by name.
    The login_session will be passed to template to control the rendered elements
     according to access rules.

    Args:
        category_id: The id of the category to be displayed.

    Raises:
        If an error occurs the application will redirect to index page and a flash message
        will be displayed with the proper Exception message.
    """
    try:
        logged_in = 'username' in login_session
        categories = db_session.query(Category).order_by(Category.name).all()
        category = db_session.query(Category).filter_by(id=category_id).one()
        items = db_session.query(Item).filter_by(category_id=category_id)\
            .order_by(Item.name).all()
        return render_template('index.html', categories=categories,
                               active_category=int(category_id), items=items,
                               logged_in=logged_in, login_session=login_session,
                               category_owner=category.user_id)
    except Exception as e:
        flash('An error has occurred: {}'.format(str(e)), 'error')
        return redirect(url_for('index'))


@app.route('/categories/<int:category_id>/items/<int:item_id>/')
def get_item_by_category(category_id, item_id):
    """ Route that renders the page for a specific item according to its category.

    The login_session will be passed to template to control the rendered elements
     according to access rules.

    Args:
        category_id: The id of the category of the item to be displayed.
        item_id: The id of the item to be displayed.

    Raises:
        If an error occurs the application will redirect to index page and a flash message
        will be displayed with the proper Exception message.
    """
    try:
        logged_in = 'username' in login_session
        categories = db_session.query(Category).order_by(Category.name).all()
        item = db_session.query(Item).filter_by(id=item_id, category_id=category_id).one()
        return render_template('items.html', categories=categories,
                               active_category=int(category_id), item=item,
                               logged_in=logged_in, login_session=login_session)
    except Exception as e:
        flash('An error has occurred: {}'.format(str(e)), 'error')
        return redirect(url_for('index'))


@app.route('/categories/<int:category_id>/items/<int:item_id>/delete/', methods=['GET', 'POST'])
def delete_item(category_id, item_id):
    """ Route that renders the page to delete an item.

    This method validate that the user is logged in, and the item were created by him, to avoid
     malicious behaviors in the url.
    The item is deleted from database and the folder created to store the uploaded images is deleted
     as well.

    Args:
        category_id: The id of the category of the item to be deleted.
        item_id: The id of the item to be deleted.

    Raises:
        If an error occurs the application will redirect to index page and a flash message
        will be displayed with the proper Exception message.
    """
    try:
        logged_in = 'username' in login_session
        if not logged_in:
            flash("You must be logged to perform this operation", category="error")
            return redirect(url_for('index'))
        item = db_session.query(Item).filter_by(id=item_id, category_id=category_id).one()
        if login_session['user_id'] != item.user_id:
            flash("You can only modify items created by you", category="error")
            return redirect(url_for('get_item_by_category', category_id=category_id,
                                    item_id=item_id))
        form = DeleteForm()
        if form.validate_on_submit():
            delete_dir('static/images/uploads/' + str(item.id))
            db_session.delete(item)
            db_session.commit()
            flash("Item '{}' successfully deleted".format(item.name))
            if category_id > 0:
                return redirect(url_for('get_category', category_id=category_id))
            else:
                return redirect(url_for('index'))
        else:
            categories = db_session.query(Category).order_by(Category.name).all()
            return render_template('delete_item.html', categories=categories,
                                   active_category=int(category_id),
                                   item=item, form=form, logged_in=logged_in,
                                   login_session=login_session)
    except Exception as e:
        flash('An error has occurred: {}'.format(str(e)), 'error')
        return redirect(url_for('index'))


@app.route('/categories/<int:category_id>/items/<int:item_id>/edit/', methods=['GET', 'POST'])
def edit_item(category_id, item_id):
    """ Route that renders the page to edit an item.

    This method validate that the user is logged in, and the item were created by him, to avoid
     malicious behaviors in the url.
    Every time the user uploads a new image, the image is stored in a folder that is named
     with the item id.
    Only one image path is stored in database.

    Args:
        category_id: The id of the category of the item to be edited.
        item_id: The id of the item to be edited.

    Raises:
        If an error occurs the application will redirect to index page and a flash message
        will be displayed with the proper Exception message.
    """
    try:
        logged_in = 'username' in login_session
        if not logged_in:
            flash("You must be logged to perform this operation", category="error")
            return redirect(url_for('index'))
        item = db_session.query(Item).filter_by(id=item_id, category_id=category_id).one()
        if login_session['user_id'] != item.user_id:
            flash("You can only modify items created by you", category="error")
            return redirect(url_for('get_item_by_category', category_id=category_id,
                                    item_id=item_id))
        form = ItemForm()
        if form.validate_on_submit():
            form.populate_obj(item)
            if len(secure_filename(form.photo.data.filename)) > 0:
                filename = 'images/uploads/' + str(item.id) + '/' + \
                           secure_filename(form.photo.data.filename)
                ensure_dir('static/' + filename)
                form.photo.data.save('static/' + filename)
                item.image_path = filename
            db_session.add(item)
            db_session.commit()
            flash("Item '{}' successfully edited".format(item.name))
            return redirect(url_for('get_item_by_category', category_id=item.category_id,
                                    item_id=item_id))
        else:
            categories = db_session.query(Category).order_by(Category.name).all()
            return render_template('edit_item.html', categories=categories,
                                   active_category=int(category_id), item=item, form=form,
                                   logged_in=logged_in, login_session=login_session)
    except Exception as e:
        flash('An error has occurred: {}'.format(str(e)), 'error')
        return redirect(url_for('index'))


@app.route('/categories/<int:category_id>/items/new/', methods=['GET', 'POST'])
def new_item(category_id):
    """ Route that renders the page to add a new item.

    This method validate that the user is logged in.
    The item is associated with the current logged in user.

    Args:
        category_id: The id of the category of the item to be added.

    Raises:
        If an error occurs the application will redirect to index page and a flash message
        will be displayed with the proper Exception message.
    """
    try:
        logged_in = 'username' in login_session
        if not logged_in:
            flash("You must be logged to perform this operation", category="error")
            return redirect(url_for('index'))
        form = ItemForm()
        item = Item()
        item.name = "New item"
        if form.validate_on_submit():
            form.populate_obj(item)
            item.user_id = login_session["user_id"]
            db_session.add(item)
            if len(secure_filename(form.photo.data.filename)) > 0:
                db_session.flush()
                filename = 'images/uploads/' + str(item.id) + '/' + \
                           secure_filename(form.photo.data.filename)
                ensure_dir('static/' + filename)
                form.photo.data.save('static/' + filename)
                item.image_path = filename
                db_session.add(item)
            db_session.commit()
            flash("Item '{}' successfully added".format(item.name))
            return redirect(url_for('get_item_by_category', category_id=item.category_id,
                                    item_id=item.id))
        else:
            categories = db_session.query(Category).order_by(Category.name).all()
            return render_template('new_item.html', categories=categories,
                                   active_category=int(category_id), item=item, form=form,
                                   logged_in=logged_in, login_session=login_session)
    except Exception as e:
        flash('An error has occurred: {}'.format(str(e)), 'error')
        return redirect(url_for('index'))


@app.route('/categories/new/', methods=['GET', 'POST'])
def new_category():
    """ Route that renders the page to add a new category.

    This method validate that the user is logged in.
    The category is associated with the current logged in user.

    Raises:
        If an error occurs the application will redirect to index page and a flash message
        will be displayed with the proper Exception message.
    """
    try:
        logged_in = 'username' in login_session
        if not logged_in:
            flash("You must be logged to perform this operation", category="error")
            return redirect(url_for('index'))
        form = CategoryForm()
        category = Category()
        category.name = "New item"
        if form.validate_on_submit():
            form.populate_obj(category)
            category.user_id = login_session["user_id"]
            db_session.add(category)
            db_session.commit()
            flash("Category '{}' successfully added".format(category.name))
            return redirect(url_for('get_category', category_id=category.id))
        else:
            categories = db_session.query(Category).order_by(Category.name).all()
            return render_template('new_category.html', categories=categories,
                                   active_category=-1, form=form, logged_in=logged_in,
                                   login_session=login_session)
    except Exception as e:
        flash('An error has occurred: {}'.format(str(e)), 'error')
        return redirect(url_for('index'))


@app.route('/categories/<int:category_id>/edit/', methods=['GET', 'POST'])
def edit_category(category_id):
    """ Route that renders the page to edit an category.

    This method validate that the user is logged in, and the category were created by him, to avoid
     malicious behaviors in the url.

    Args:
        category_id: The id of the category to be edited.

    Raises:
        If an error occurs the application will redirect to index page and a flash message
        will be displayed with the proper Exception message.
    """
    try:
        logged_in = 'username' in login_session
        if not logged_in:
            flash("You must be logged to perform this operation", category="error")
            return redirect(url_for('index'))
        category = db_session.query(Category).filter_by(id=category_id).one()
        if login_session['user_id'] != category.user_id:
            flash("You can only modify categories created by you", category="error")
            return redirect(url_for('get_category', category_id=category_id))
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
                                   active_category=category_id, form=form, logged_in=logged_in,
                                   login_session=login_session)
    except Exception as e:
        flash('An error has occurred: {}'.format(str(e)), 'error')
        return redirect(url_for('index'))


@app.route('/categories/<int:category_id>/delete/', methods=['GET', 'POST'])
def delete_category(category_id):
    """ Route that renders the page to delete a category.

    This method validate that the user is logged in, and the category were created by him, to avoid
     malicious behaviors in the url.
    The category is deleted from database and all the items that belongs to this category are deleted
     in cascade, as well as all the images associated with the items.
    All the items are deleted even if weren't created for this user, it is enough to be the owner of
     the category.

    Args:
        category_id: The id of the category to be deleted.

    Raises:
        If an error occurs the application will redirect to index page and a flash message
        will be displayed with the proper Exception message.
    """
    try:
        logged_in = 'username' in login_session
        if not logged_in:
            flash("You must be logged to perform this operation", category="error")
            return redirect(url_for('index'))
        category = db_session.query(Category).filter_by(id=category_id).one()
        if login_session['user_id'] != category.user_id:
            flash("You can only modify categories created by you", category="error")
            return redirect(url_for('get_category', category_id=category_id))
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
            return render_template('delete_category.html', categories=categories,
                                   active_category=int(category_id), category=category,
                                   form=form, logged_in=logged_in, login_session=login_session)
    except Exception as e:
        flash('An error has occurred: {}'.format(str(e)), 'error')
        return redirect(url_for('index'))


@app.route('/json/categories/')
def json_api_categories():
    """ Route to render the page for JSON Api.

    It will render all the information relative of the categories in a single response.

    Raises:
        If an error occurs the application will generate a JSON response
        with the proper Exception message.
    """
    try:
        categories = db_session.query(Category).order_by(Category.name).all()
        return jsonify(categories=[r.serialize for r in categories])
    except Exception as e:
        response = make_response(json.dumps('An error has occurred {}'.format(str(e)), 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/json/categories/<int:category_id>/items/')
def json_api_get_category(category_id):
    """ Route to render the page for JSON Api for a specified category.

    It will render all the information relative to one category only.

    Args:
        category_id: The id of the category to be displayed.

    Raises:
        If an error occurs the application will generate a JSON response
        with the proper Exception message.
    """
    try:
        items = db_session.query(Item).filter_by(category_id=category_id).order_by(Item.name).all()
        return jsonify(items=[r.serialize for r in items])
    except Exception as e:
        response = make_response(json.dumps('An error has occurred {}'.format(str(e)), 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/json/items/')
def json_api_items():
    """ Route to render the page for JSON Api for all the items.

    It will render all the information relative of all items in a single response.

    Raises:
        If an error occurs the application will generate a JSON response
        with the proper Exception message.
    """
    try:
        items = db_session.query(Item).order_by(desc(Item.modified_date)).all()
        return jsonify(items=[r.serialize for r in items])
    except Exception as e:
        response = make_response(json.dumps('An error has occurred {}'.format(str(e)), 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/json/items/<int:item_id>/')
def json_api_get_item(item_id):
    """ Route to render the page for JSON Api for a specified item.

    It will render all the information relative to one item only.

    Args:
        item_id: The id of the item to be displayed.

    Raises:
        If an error occurs the application will generate a JSON response
        with the proper Exception message.
    """
    try:
        item = db_session.query(Item).filter_by(id=item_id).one()
        return jsonify(item.serialize)
    except Exception as e:
        response = make_response(json.dumps('An error has occurred {}'.format(str(e)), 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/json/categories/<int:category_id>/items/<int:item_id>/')
def json_api_get_item_by_category(category_id, item_id):
    """ Route to render the page for JSON Api for a specified item.

    It will render all the information relative to one item only.

    Args:
        item_id: The id of the item to be displayed.
        category_id: The id of the category that contains the item to be displayed.

    Raises:
        If an error occurs the application will generate a JSON response
        with the proper Exception message.
    """
    try:
        item = db_session.query(Item).filter_by(id=item_id, category_id=category_id).one()
        return jsonify(item.serialize)
    except Exception as e:
        response = make_response(json.dumps('An error has occurred {}'.format(str(e)), 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/xml/categories/')
def xml_api_categories():
    """ Route to render the page for XML Api.

    It will render all the information relative of the categories in a single response.

    Raises:
        If an error occurs the application will generate a XML response
        with the proper Exception message.
    """
    try:
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
                item_user_id = SubElement(items, 'user_id')
                item_user_id.text = str(item.user_id)
        return app.response_class(tostring(data), mimetype='application/xml')
    except Exception as e:
        data = Element('error')
        data.text = str(e)
        return app.response_class(tostring(data), mimetype='application/xml')


@app.errorhandler(404)
def page_not_found(error):
    """ If a page is not found the application will redirect to index page and a flash message
        will be displayed with an error Flash message.
    """
    flash('Page not found: {}'.format(request.path), "error")
    return redirect(url_for('index'))


def create_user():
    """ Method that will create an user .
    Returns:
        user.id: The id of the created user
    Raises:
        If an error occurs it will be displayed in a error message.
    """
    try:
        new_user = User(name=login_session['username'], email=login_session[
                       'email'], picture=login_session['picture'])
        db_session.add(new_user)
        db_session.commit()
        user = db_session.query(User).filter_by(email=login_session['email']).one()
        return user.id
    except Exception as e:
        flash('An error has occurred: {}'.format(str(e)), 'error')
        return None


def get_user_info(user_id):
    """ Method that will get an user info.

    Args:
        user_id: The id of the user to be found.
    Returns:
        user: The user object from database
    Raises:
        If an error occurs it will be displayed in a error message.
    """
    try:
        user = db_session.query(User).filter_by(id=user_id).one()
        return user
    except Exception as e:
        flash('An error has occurred: {}'.format(str(e)), 'error')
        return None


def get_user_id(email):
    """ Method that will get an user id from an email.

    Args:
        email: The email of the user to be found.
    Returns:
        user.id: The user id from database
    Raises:
        If an error occurs it will be displayed in a error message.
    """
    try:
        user = db_session.query(User).filter_by(email=email).one()
        return user.id
    except Exception as e:
        flash('An error has occurred: {}'.format(str(e)), 'error')
        return None


if __name__ == '__main__':
    app.secret_key = 'super_secret_key_for_catalog_item'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
