from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from .models import *
from .query import *
from werkzeug.security import check_password_hash, generate_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user, user_logged_out
import requests
import json
from .nutritionX import find_nutrition

auth = Blueprint("auth", __name__)


@auth.route("/login.html", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        login_password = request.form.get("login_password")

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, login_password):
                #flash("Logged in successfully!", category="success")
                login_user(user, remember=True)
                return redirect(url_for('auth.profile', user=user))
            else:
                flash("Incorrect password, try again.", category="error")
        else:
            flash("Email does not exist.", category="error")

    return render_template("login.html", user=current_user)


@auth.route("/signup.html", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        global email
        email = request.form.get("email")
        global signup_password1
        signup_password1 = request.form.get("signup_password1")
        signup_password2 = request.form.get("signup_password2")

        global user
        user = User.query.filter_by(email=email).first()

        if user:
            flash("Email already Exists", category="error")
        elif "." not in email:
            flash("Enter valid Email", category="error")
        elif len(email) < 5:
            flash("Enter valid Email", category="error")
        elif len(signup_password1) < 7:
            flash("Password should be greater than 7 character", category="error")
        elif signup_password1 != signup_password2:
            flash("Password Does Not Match", category="error")
        elif len(signup_password1) > 149:
            flash("Password is too long", category="error")
        elif len(email) > 149:
            flash("Email is too long", category="error")
        else:
            global new_user
            new_user = User(
                email=email,
                password=generate_password_hash(signup_password1, method="scrypt"),
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            # flash('Account Created!', category='success')
            return redirect(url_for("auth.info", user=new_user))
    return render_template("signup.html", user=current_user)


@auth.route("/info", methods=["GET", "POST"])
@login_required
def info(user=None):
    if request.method == "POST":
        user = new_user

        name = request.form.get("name")
        age = request.form.get("age")
        gender = request.form.get("gender")
        weight = request.form.get("weight")
        height = request.form.get("height")
        activity_level = request.form.get("activity_level")

        # print(name)
        # print(age)
        # print(gender)
        # print(weight)
        # print(height)
        # print(activity_level)

        # Ensure "gender" is provided
        if gender is None:
            flash("Please provide your gender", category="error")
            return render_template("info.html")

        new_user_info = Info(
            name=name,
            age=age,
            gender=gender,
            weight=weight,
            height=height,
            activity_level=activity_level,
            user_id=current_user.id,
        )

        try:
            db.session.add(new_user_info)
            db.session.commit()
            print(new_user_info)
        except Exception as e:
            # Print or log the exception to see if there's a specific database issue
            print(str(e))
        login_user(user, remember=True)
        flash("Account Created!", category="success")
        return render_template("profile.html", user=current_user)

    return render_template("info.html")


@auth.route("/profile.html", methods=["GET", "POST"])
@login_required
def profile(user=None):
    bmr = 0
    tdee = 0
    height = get_user_height(current_user)
    weight = get_user_weight(current_user)
    age = get_user_age(current_user)
    gender = get_user_gender(current_user)
    name = get_user_first_name(current_user)

    if None in (height, weight, age, gender):
        # Handle the case where user data is missing
        flash("User data is incomplete", category="error")
        return render_template("profile.html", user=user)
    if gender == "MALE":
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        
    activity_level = get_user_activity_level(current_user)
    
    if activity_level == "very low":
        tdee = bmr * 1.2
    elif activity_level == "low":
        tdee = bmr * 1.375
    elif activity_level == "medium":
        tdee = bmr * 1.55
    else:
        tdee = bmr * 1.725
        
    if request.method == "POST":
        food_name = request.form.get("food_name")
        try:
            nutrition_info = find_nutrition(food_name)
            if len(nutrition_info) == 2:
                render_template("profile.html", user=user, bmr=bmr, tdee=tdee)
        except:
            render_template("profile.html", user=user)
            
        if "foods" in nutrition_info and len(nutrition_info["foods"]) > 0:
            nutrition_info = nutrition_info["foods"][0]
            data = {
            "food_name": nutrition_info["food_name"],
            "nf_calories": nutrition_info["nf_calories"],
            "carbohydrate": nutrition_info["nf_total_carbohydrate"],
            "protein": nutrition_info["nf_protein"],
            "fat": nutrition_info["nf_total_fat"],
            "photo": nutrition_info["photo"]["thumb"],
            }
            #print(data)
            return render_template("profile.html", data=data, user=user, bmr=bmr, tdee=tdee, name=name)
        else:
            flash("You typed Wrong Spelling", category="error")
            return render_template("profile.html", user=user, bmr=bmr, tdee=tdee, name=name)
        
        
        #return jsonify(data)
        #return redirect(url_for("auth.profile", data=data))
        
        
    return render_template("profile.html", user=user, bmr=bmr, tdee=tdee, name=name)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("views.home"))
