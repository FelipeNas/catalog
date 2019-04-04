#!/usr/bin/env python2
from flask import (
    Flask, render_template, request, redirect, url_for, flash, jsonify,
    make_response)
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem
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
    return render_template(
        "restaurants.html", restaurants=restaurants)


@app.route("/restaurant/new", methods=["GET", "POST"])
def newRestaurant():
    # This page will be for making a new restaurant
    if request.method == 'POST':
        newRestaurant = Restaurant(name=request.form["name"])
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


@app.route("/restaurant/<int:restaurant_id>/delete", methods=["GET", "POST"])
def deleteRestaurant(restaurant_id):
    # This page will be for deleting restaurant
    deletingRestaurant = session.query(
        Restaurant).filter_by(id=restaurant_id).one()
    if request.method == "POST":
        session.delete(deletingRestaurant)
        session.commit()
        flash("Restaurant successfully deleted")
        return redirect(url_for("showRestaurants"))
    else:
        return render_template(
            "deleteRestaurant.html", restaurant=deletingRestaurant)

@app.route("/restaurant/<int:restaurant_id>/")
@app.route("/restaurant/<int:restaurant_id>/menu")
def showMenu(restaurant_id):
    # This page is the menu for restaurant
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)
    return render_template(
        "menu.html", restaurant=restaurant, items=items)


@app.route("/restaurant/<int:restaurant_id>/menu/new", methods=["GET", "POST"])
def newMenuItem(restaurant_id):
    # This page is for making a new menu item for restaurant
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
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


@app.route(
    "/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit",
    methods=["GET", "POST"])
def editMenuItem(restaurant_id, menu_id):
    # This page is for editing menu item
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
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


@app.route(
    "/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete",
    methods=["GET", "POST"])
def deleteMenuItem(restaurant_id, menu_id):
    # This page is for deleting menu item
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == "POST":
        session.delete(itemToDelete)
        session.commit()
        flash("Menu item successfully deleted")
        return redirect(url_for("showMenu", restaurant_id=restaurant_id))
    else:
        return render_template("deleteMenuItem.html", item=itemToDelete)

if __name__ == "__main__":
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host="0.0.0.0", port=8000)
