from flask import Flask, render_template, url_for, request, redirect, flash, jsonify, session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

__author__ = 'Sotsir'

app = Flask(__name__)

engine = create_engine('sqlite:///item_catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
db_session = DBSession()


@app.route('/')
def index():
    return render_template('index.html', logged_in=False)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key_for_catalog_item'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
