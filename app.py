from flask import Flask, render_template, request, url_for, flash, redirect

import requests
import os

from product_data_parser import ProductDataParser
from supermarket import SupermarketAPI

# Create the Flask application
app = Flask(__name__)
DEBUG = True
GEOCODER_API_KEY = os.getenv("GEOCODER_API_KEY")

# Define the route for the index page
@app.route("/")
def index():
    # Render the index.html template in the /templates directory
    return render_template("index.html")


@app.route("/search", methods=("GET", "POST"))
def search():
    print(request)
    if "query" and "postal_code" in request.form:
        query = request.form["query"]
        postal_code = request.form["postal_code"]

        # Look up users postal code, convert to lat & long to search for user's local stores
        # Get each store's normalized data using ProductDataParser
        products_data = SupermarketAPI(query)
        parser = ProductDataParser

        if postal_code is None:
            raise Exception("Postal code is required")

        if DEBUG is True:
            longitude = "-115.02"
            latitude = "49.509724"
        else:
            longitude, latitude = lookup_postal_code(postal_code)

        if latitude is None:
            raise Exception("No geo coords!")

        d = products_data.search_stores_pc(
            latitude, longitude, store_brand="superstore"
        )
        pc_store_id = d["ResultList"][0]["Attributes"][0]["AttributeValue"]

        e = products_data.search_stores_saveon(latitude, longitude)
        saveon_store_id = e["items"][0]["retailerStoreId"]

        # Set default stores (closest store)
        products_data.set_store_pc(pc_store_id)
        products_data.set_store_saveon(saveon_store_id)
        products_data.set_store_walmart(latitude, longitude, postal_code)

        # Search stores for query
        a = products_data.query_pc()
        b = products_data.query_safeway()
        c = products_data.query_saveon()
        f = products_data.query_walmart()

        search_data = {
            "store_name": {
                "pc": d["ResultList"][0]["Name"],
                "saveon": e["items"][0]["name"],
                "safeway": "safewaySTORENAME",
                "walmart": postal_code,
            },
            "results": {
                "safeway": parser.parse_safeway_json_data(b),
                "saveon": parser.parse_saveonfoods_json_data(c),
                "pc": parser.parse_pc_json_data(a),
                "walmart": parser.parse_walmart_json_data(f),
            },
        }

        return render_template("search.html", result_data=search_data)


# Look up postal code to lat,long coords
def lookup_postal_code(postal_code):
    url = (
        "https://geocoder.ca/?postal={postal_code}&auth="
        + GEOCODER_API_KEY
        + "&geoit=XML".format(postal_code=postal_code)
    )
    response = requests.get(url)
    if response.status_code == 200:
        data = response.text
        longitude = data.split("<longt>")[1].split("</longt>")[0]
        latitude = data.split("<latt>")[1].split("</latt>")[0]
        return longitude, latitude


# Run the app
if __name__ == "__main__":
    app.run()
