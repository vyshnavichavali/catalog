from flask import Flask, render_template, url_for
from flask import request, redirect, flash, make_response, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Data_Setup import Base, GoldCompanyName, GoldName, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
import datetime

engine = create_engine('sqlite:///Gold.db',
                       connect_args={'check_same_thread': False}, echo=True)
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']
APPLICATION_NAME = "Gold Store"

DBSession = sessionmaker(bind=engine)
session = DBSession()
# Create anti-forgery state token
va_cat = session.query(GoldCompanyName).all()


# login
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    va_cat = session.query(GoldCompanyName).all()
    tbes = session.query(GoldName).all()
    return render_template('login.html',
                           STATE=state, va_cat=va_cat, tbes=tbes)
    # return render_template('myhome.html', STATE=state
    # va_cat=va_cat,tbes=tbes)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px; border-radius: 150px;'
    '-webkit-border-radius: 150px; -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output


# User Helper Functions
def createUser(login_session):
    User1 = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(User1)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception as error:
        print(error)
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session

#####
# Home


@app.route('/')
@app.route('/home')
def home():
    va_cat = session.query(GoldCompanyName).all()
    return render_template('myhome.html', va_cat=va_cat)

#####
# Gold Category for admins


@app.route('/GoldStore')
def GoldStore():
    try:
        if login_session['username']:
            name = login_session['username']
            va_cat = session.query(GoldCompanyName).all()
            va = session.query(GoldCompanyName).all()
            tbes = session.query(GoldName).all()
            return render_template('myhome.html', va_cat=va_cat,
                                   va=va, tbes=tbes, uname=name)
    except:
        return redirect(url_for('showLogin'))

######
# Showing Gold based on Gold category


@app.route('/GoldStore/<int:tbid>/AllCompanys')
def showGold(tbid):
    va_cat = session.query(GoldCompanyName).all()
    va = session.query(GoldCompanyName).filter_by(id=tbid).one()
    tbes = session.query(GoldName).filter_by(goldcompanynameid=tbid).all()
    try:
        if login_session['username']:
            return render_template('showGold.html', va_cat=va_cat,
                                   va=va, tbes=tbes,
                                   uname=login_session['username'])
    except:
        return render_template('showGold.html',
                               va_cat=va_cat, va=va, tbes=tbes)

#####
# Add New gold


@app.route('/GoldStore/addGoldCompany', methods=['POST', 'GET'])
def addGoldCompany():
    if request.method == 'POST':
        company = GoldCompanyName(name=request.form['name'],
                                  user_id=login_session['user_id'])
        session.add(company)
        session.commit()
        return redirect(url_for('GoldStore'))
    else:
        return render_template('addGoldCompany.html', va_cat=va_cat)

########
# Edit Gold Category


@app.route('/GoldStore/<int:tbid>/edit', methods=['POST', 'GET'])
def editGoldCategory(tbid):
    editedGold = session.query(GoldCompanyName).filter_by(id=tbid).one()
    creator = getUserInfo(editedGold.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot edit this Gold Category."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('GoldStore'))
    if request.method == "POST":
        if request.form['name']:
            editedGold.name = request.form['name']
        session.add(editedGold)
        session.commit()
        flash("Gold Category Edited Successfully")
        return redirect(url_for('GoldStore'))
    else:
        # va_cat is global variable we can them in entire application
        return render_template('editGoldCategory.html',
                               tb=editedGold, va_cat=va_cat)

######
# Delete Gold Category


@app.route('/GoldStore/<int:tbid>/delete', methods=['POST', 'GET'])
def deleteGoldCategory(tbid):
    tb = session.query(GoldCompanyName).filter_by(id=tbid).one()
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot Delete this Gold Category."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('GoldkStore'))
    if request.method == "POST":
        session.delete(tb)
        session.commit()
        flash("Gold Category Deleted Successfully")
        return redirect(url_for('GoldStore'))
    else:
        return render_template('deleteGoldCategory.html',
                               tb=tb, va_cat=va_cat)
######
# Add New Gold Name Details


@app.route('/GoldStore/addCompany/addGoldDetails/<string:tbname>/add',
           methods=['GET', 'POST'])
def addGoldDetails(tbname):
    va = session.query(GoldCompanyName).filter_by(name=tbname).one()
    # See if the logged in user is not the owner of gold
    creator = getUserInfo(va.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't add new book edition"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showGold', tbid=va.id))
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        discount = request.form['discount']
        golddetails = GoldName(name=name, price=price,
                               discount=discount,
                               date=datetime.datetime.now(),
                               goldcompanynameid=va.id,
                               user_id=login_session['user_id'])
        session.add(golddetails)
        session.commit()
        return redirect(url_for('showGold', tbid=va.id))
    else:
        return render_template('addGoldDetails.html',
                               tbname=va.name, va_cat=va_cat)

######
# Edit Gold details


@app.route('/GoldStore/<int:tbid>/<string:tbename>/edit',
           methods=['GET', 'POST'])
def editGold(tbid, tbename):
    tb = session.query(GoldCompanyName).filter_by(id=tbid).one()
    golddetails = session.query(GoldName).filter_by(name=tbename).one()
    # See if the logged in user is not the owner of gold
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't edit this book edition"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showGold', tbid=tb.id))
    # POST methods
    if request.method == 'POST':
        golddetails.name = request.form['name']
        golddetails.price = request.form['price']
        golddetails.discount = request.form['discount']
        golddetails.date = datetime.datetime.now()
        session.add(golddetails)
        session.commit()
        flash("Gold Edited Successfully")
        return redirect(url_for('showGold', tbid=tbid))
    else:
        return render_template('editGold.html',
                               tbid=tbid, golddetails=golddetails,
                               va_cat=va_cat)

#####
# Delte gold Edit


@app.route('/GoldkStore/<int:tbid>/<string:tbename>/delete',
           methods=['GET', 'POST'])
def deleteGold(tbid, tbename):
    tb = session.query(GoldCompanyName).filter_by(id=tbid).one()
    golddetails = session.query(GoldName).filter_by(name=tbename).one()
    # See if the logged in user is not the owner of gold
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't delete this book edition"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('Gold', tbid=tb.id))
    if request.method == "POST":
        session.delete(golddetails)
        session.commit()
        flash("Deleted Gold Successfully")
        return redirect(url_for('showGold', tbid=tbid))
    else:
        return render_template('deleteGold.html',
                               tbid=tbid, golddetails=golddetails,
                               va_cat=va_cat)

####
# Logout from current user


@app.route('/logout')
def logout():
    access_token = login_session['access_token']
    print ('In gdisconnect access token is %s', access_token)
    print ('User name is: ')
    print (login_session['username'])
    if access_token is None:
        print ('Access Token is None')
        response = make_response(
            json.dumps('Current user not connected....'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = \
        h.request(uri=url, method='POST', body=None,
                  headers={'content-type':
                           'application/x-www-form-urlencoded'})[0]
    print (result['status'])
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps
                                 ('Successfully disconnected user..'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("Successful logged out")
        return redirect(url_for('home'))
    # return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

#####
# Json


@app.route('/GoldStore/JSON')
def allGoldsJSON():
    goldcategories = session.query(GoldCompanyName).all()
    category_dict = [c.serialize for c in goldcategories]
    for c in range(len(category_dict)):
        gold = [i.serialize for i in session.query(
                 GoldName).filter_by(goldcompanynameid=category_dict[c]["id"])
                .all()]
        if gold:
            category_dict[c]["gold"] = gold
    return jsonify(GoldCompanyName=category_dict)

####


@app.route('/goldStore/goldCategories/JSON')
def categoriesJSON():
    gold = session.query(GoldCompanyName).all()
    return jsonify(goldCategories=[c.serialize for c in gold])

####


@app.route('/goldStore/gold/JSON')
def itemsJSON():
    items = session.query(GoldName).all()
    return jsonify(gold=[i.serialize for i in items])

#####


@app.route('/goldStore/<path:gold_name>/gold/JSON')
def categoryItemsJSON(gold_name):
    goldCategory = session.query(GoldCompanyName).filter_by(
                   name=gold_name).one()
    gold = session.query(GoldName).filter_by(
           goldcompanyname=goldCategory).all()
    return jsonify(goldEdtion=[i.serialize for i in gold])

#####


@app.route('/goldStore/<path:gold_name>/<path:edition_name>/JSON')
def ItemJSON(gold_name, edition_name):
    goldCategory = session.query(GoldCompanyName).filter_by(
                   name=gold_name).one()
    goldEdition = session.query(GoldName).filter_by(
           name=edition_name, goldcompanyname=goldCategory).one()
    return jsonify(goldEdition=[goldEdition.serialize])

if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host='127.0.0.1', port=8000)
