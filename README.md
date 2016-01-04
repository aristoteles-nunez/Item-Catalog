# Table of Contents
* [Item's catalog](#items-catalog)
* [Features](#features)
* [ToDo](#todo)
* [Prerequisites](#prerequisites)
    * [Installed software on your operating system](#installed-software-on-your-operating-system)
        * [Native installation](#native-installation)
        * [Using Vagrant](#using-vagrant)
    * [Installation process](#installation-process)
    * [Configure Google Oauth credentials](#configure-google-oauth-credentials)
    * [Database Creation](#database-creation)
        * [Populate with sample data](#populate-with-sample-data)
* [Program Execution](#program-execution)
* [API Endpoints](#api-endpoints)
    * [JSON Api](#json-api)
    * [XML Api](#xml-api)
* [License](#license)

# Item's catalog
Project that display a set of categories with their respectives items.

# Features
 
* Read operation to all categoris for non registered users.
* Permissions to add new items/categories only for registered users.
* Permissions to Edit / Delete each item/category only for owners of the items.
* Prevent cross-site request forgeries (CSRF) with `WTForms`.
* User registration and authentication using Google Oauth.
* Database persistence using `PostgreSQL`.
* JSON Endpoint.
* XML Endpoint.

# ToDo
* Create user's roles

# Prerequisites

## Installed software on your operating system

You can choose between native installation or use a virtual machine with Vagrant: 

### Native installation
* `Python 3.X` along with `pip3`
* `PostgreSQL 9.0` or higher. View [PostgreSQL Download and Install Instructions][2]
* `Psycopg` adapter. Psycopg is a PostgreSQL adapter for the Python programming language.
 View [Psycopg Install Instructions][3]
 
### Using Vagrant
If you don't want to install the software on your machine you can use a virtual machine using Vagrant, in that case
you must have installed on your system:

* Virtual Box. [Download virtualbox][4] and install it. You do not need the extension pack or the SDK. 
You do not need to launch VirtualBox after installing it
* Vagrant. [Download vagrant][5] and install it.

Once you have the software installed go into the project folder and execute:

```
vagrant up
```

And loggin into the virtual machine using: 

```
vagrant ssh
```

To stop the virtual machine execute:

```
vagrant halt
```

## Installation process
Once you have [Installed software on your operating system](#installed-software-on-your-operating-system), move 
**inside project folder** and install prerequisites through one of the following commands according to your 
system (remember we are using python3):
    
```
pip3 install -r requirements.txt
```

or

```
pip install -r requirements.txt
```

**Note:** In some systems admin privileges are required.

## Configure Google Oauth credentials
You need to configure your own credentials to use Google Oauth authentication

1. Go to [http://console.developers.google.com][9]
1. Create a `New Project` or choose an existent one.
1. Go to: `Use Google APIs`.
1. Go to:  `Credentials`.
1. Fill up `Oauth Consent Screen` Form.
1. Click on: `New credentials` and `Oath Client ID`.
1. Choose `Web application`.
1. Fill up with the correct information.
    * Name: `Item-Catalog`.
    * Authorized JavaScript origins: `http://localhost:5000`
1. Get the generated credentials with one of the following steps.
    * Copy `client_id` and `client_secret` and replace it into `client_secret.json` file or:
    * Download `JSON file` with name `client_secret.json` and replace the existing one into the project folder.

## Database Creation
The main progam will try to automatically create the `item_catalog` database if it doesn't already exist, so make sure
your actual user has the right level permission to perform database creation, and this database name does not make 
conflict with existing databases.

### Populate with sample data
Some sample data it is included, so if you want to populate the database with the sample data, inside the project folder,
execute:

```
python3 insert_sample_data.py
```

**Note:** The items added in this sample data won't be editable at least you change the user email associate with them, 
using the email of your Google Oauth account.

# Program Execution
Once you have completed all [Prerequisites](#prerequisites) you can move inside project folder and execute 
one of the following commands (according to your system) to launch the webapp:

```
python3 app.py
```

or

```
python app.py
```

Now you can use the app on your browser with: [http://localhost:5000][6]

# API Endpoints

You can obtain the all the information using the following endpoints 

## JSON Api
[http://localhost:5000/json/categories/][7]

## XML Api
[http://localhost:5000/xml/categories/][8]

# License

[The MIT License (MIT)][1]

[1]: LICENSE
[2]: http://www.postgresql.org/download/
[3]: http://initd.org/psycopg/docs/install.html
[4]: https://www.virtualbox.org/wiki/Downloads
[5]: https://www.vagrantup.com/downloads
[6]: http://localhost:5000
[7]: http://localhost:5000/json/categories/
[8]: http://localhost:5000/xml/categories/
[9]: http://console.developers.google.com