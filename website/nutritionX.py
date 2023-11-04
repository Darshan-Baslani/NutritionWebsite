import requests
import json
from flask import render_template
from flask_login import current_user

def find_nutrition(food_name):
    url = "https://trackapi.nutritionix.com/v2/natural/nutrients"

    headers = {
        'x-app-id' : 'd5bd0711',
        'x-app-key' : 'c8b6f411efafe4b2e15825983bb2352b'
    }
    
    parameters = {
        'query' : food_name
    }
    try:
        response = requests.post(url, headers=headers, json=parameters)
    except:
        return render_template("profile.html", user=current_user)
    return response.json()