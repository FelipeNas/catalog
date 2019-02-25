#!/usr/bin/env python2
from flask import (
    Flask, render_template, request, redirect, url_for, flash, jsonify,
    make_response)
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import random
import requests
import string


app = Flask(__name__)

engine = create_engine(
    "sqlite:///catalog.db",
    connect_args={"check_same_thread": False})

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(
    open("client_secrets.json", "r").read())["web"]["client_id"]


def createUser(login_session):
    newUser = User(
        name=login_session["username"],
        email=login_session["email"],
        picture=login_session["picture"])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session["email"]).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route("/login")
def showLogin():
    # Login page with token
    state = "".join(
        random.choice(string.ascii_uppercase + string.digits)
        for x in xrange(32))
    login_session["state"] = state
    return render_template("login.html", STATE=state)


@app.route("/gconnect", methods=["POST"])
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
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200
        )
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

    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '"style = "width: 300px; height: 300px; border-radius: 150px;' \
        '-webkit-border-radius: 150px; -moz-border-radius: 150px;">'
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    # Disconnecting from Google Auth
    print login_session
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % \
        login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if access_token is not None:
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(
            json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for("showRestaurants"))
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route("/restaurants/JSON")
def restaurantsJSON():
    # API for all restaurants
    restaurants = session.query(Restaurant).all()
    return jsonify(Restaurants=[rest.serialize for rest in restaurants])


@app.route("/restaurant/<int:restaurant_id>/JSON")
def OneRestaurantJSON(restaurant_id):
    # API for one restaurants
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    return jsonify(Restaurant=[restaurant.serialize])


@app.route("/restaurant/<int:restaurant_id>/menu/JSON")
def restaurantMenuJSON(restaurant_id):
    # API for all Menu Items
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route("/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON")
def OneItemMenuJSON(restaurant_id, menu_id):
    # API for one Menu Item
    items = session.query(MenuItem).filter_by(
        id=menu_id).one()
    return jsonify(MenuItem=[items.serialize])


@app.route("/")
@app.route("/restaurants")
def showRestaurants():
    # This page will show all restaurants
    restaurants = session.query(Restaurant).all()
    users = session.query(User).all()
    return render_template(
        "restaurants.html", restaurants=restaurants, users=users)


@app.route("/restaurant/new", methods=["GET", "POST"])
def newRestaurant():
    # This page will be for making a new restaurant
    if request.method == 'POST':
        newRestaurant = Restaurant(
            name=request.form["name"],
            user_id=login_session['user_id'])
        session.add(newRestaurant)
        session.commit()
        flash("New restaurant created")
        return redirect(url_for("showRestaurants"))
    else:
        return render_template("newRestaurant.html")


@app.route("/restaurant/<int:restaurant_id>/edit", methods=["GET", "POST"])
def editRestaurant(restaurant_id):
    # This page will be for editing restaurant
    editedRestaurant = session.query(
        Restaurant).filter_by(id=restaurant_id).one()
    if login_session['user_id'] == editedRestaurant.user_id:
        if request.method == "POST":
            if request.form["name"]:
                editedRestaurant.name = request.form["name"]
                session.add(editedRestaurant)
                session.commit()
                flash("Restaurant successfully edited")
                return redirect(url_for("showRestaurants"))
        else:
            return render_template(
                "editRestaurant.html", restaurant=editedRestaurant)
    else:
        flash("You're not the owner of the restaurant")
        return redirect(url_for("showRestaurants"))


@app.route("/restaurant/<int:restaurant_id>/delete", methods=["GET", "POST"])
def deleteRestaurant(restaurant_id):
    # This page will be for deleting restaurant
    deletingRestaurant = session.query(
        Restaurant).filter_by(id=restaurant_id).one()
    if login_session['user_id'] == deletingRestaurant.user_id:
        if request.method == "POST":
            session.delete(deletingRestaurant)
            session.commit()
            flash("Restaurant successfully deleted")
            return redirect(url_for("showRestaurants"))
        else:
            return render_template(
                "deleteRestaurant.html", restaurant=deletingRestaurant)
    else:
        flash("You're not the owner of the restaurant")
        return redirect(url_for("showRestaurants"))


@app.route("/restaurant/<int:restaurant_id>/")
@app.route("/restaurant/<int:restaurant_id>/menu")
def showMenu(restaurant_id):
    # This page is the menu for restaurant
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
    creator = getUserInfo(restaurant.user_id)
    return render_template(
        "menu.html", restaurant=restaurant, items=items, creator=creator)


@app.route("/restaurant/<int:restaurant_id>/menu/new", methods=["GET", "POST"])
def newMenuItem(restaurant_id):
    # This page is for making a new menu item for restaurant
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if login_session['user_id'] == restaurant.user_id:
        if request.method == "POST":
            if request.form["name"]:
                newItem = MenuItem(
                    name=request.form["name"],
                    description=request.form["description"],
                    price=request.form["price"],
                    course=request.form["course"],
                    restaurant_id=restaurant_id)
                session.add(newItem)
                session.commit()
                flash("New menu item created")
                return redirect(
                    url_for("showMenu", restaurant_id=restaurant_id))
            else:
                return redirect(
                    url_for("showMenu", restaurant_id=restaurant_id))
        else:
            return render_template("newMenuItem.html", restaurant=restaurant)
    else:
        flash("You're not the owner of the restaurant")
        return redirect(url_for("showMenu", restaurant_id=restaurant_id))


@app.route(
    "/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit",
    methods=["GET", "POST"])
def editMenuItem(restaurant_id, menu_id):
    # This page is for editing menu item
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
    if login_session['user_id'] == restaurant.user_id:
        if request.method == "POST":
            if request.form["name"]:
                editedItem.name = request.form["name"]
                session.add(editedItem)
                session.commit()
            if request.form["description"]:
                editedItem.description = request.form["description"]
                session.add(editedItem)
                session.commit()
            if request.form["price"]:
                editedItem.price = request.form["price"]
                session.add(editedItem)
                session.commit()
            if request.form["course"]:
                editedItem.course = request.form["course"]
                session.add(editedItem)
                session.commit()
                flash("Menu item successfully edited")
                return redirect(
                    url_for("showMenu", restaurant_id=restaurant_id))
        else:
            return render_template(
                "editMenuItem.html",
                restaurant=restaurant,
                item=editedItem
            )
    else:
        flash("You're not the owner of the restaurant")
        return redirect(url_for("showMenu", restaurant_id=restaurant_id))


@app.route(
    "/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete",
    methods=["GET", "POST"])
def deleteMenuItem(restaurant_id, menu_id):
    # This page is for deleting menu item
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one()
    if login_session['user_id'] == restaurant.user_id:
        if request.method == "POST":
            session.delete(itemToDelete)
            session.commit()
            flash("Menu item successfully deleted")
            return redirect(url_for("showMenu", restaurant_id=restaurant_id))
        else:
            return render_template("deleteMenuItem.html", item=itemToDelete)
    else:
        flash("You're not the owner of the restaurant")
        return redirect(url_for("showMenu", restaurant_id=restaurant_id))

if __name__ == "__main__":
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host="0.0.0.0", port=8000)
