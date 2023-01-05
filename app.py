from flask import Flask, render_template, request, url_for, flash, redirect

import requests



from product_data_parser import ProductDataParser
from supermarket import SupermarketAPI

# Create the Flask application
app = Flask(__name__)

# Define the route for the index page
@app.route("/")
def index():
    # Render the index.html template in the /templates directory
    return render_template("index.html")


@app.route("/search", methods=("GET", "POST"))
def search():
    print(request)
    if "query" in request.form:
        query = request.form["query"]
        postal_code = request.form["postal_code"]
        print(query)

        # Look up users postal code, convert to lat & long for Presidents choice
        # Get each store's normalized data using ProductDataParser
        products_data = SupermarketAPI(query)
        parser = ProductDataParser

        longitude, latitude = lookup_postal_code(postal_code)

        d = products_data.search_stores_pc(latitude,longitude)
        pc_store_id = d['ResultList'][0]['Attributes'][0]['AttributeValue']
        #pc_store_name = d['ResultList'][0]['Name']
        products_data.set_store_pc(pc_store_id)

        a = products_data.query_pc()

        b = products_data.query_safeway()
        c = products_data.query_saveon()

        search_data = {
            "safeway": parser.parse_safeway_json_data(b),
            "saveon": parser.parse_saveonfoods_json_data(c),
            "pc": parser.parse_pc_json_data(a),
        }
        # print(gg)
        return render_template("search.html", result_data=search_data)

#Look up postal code to lat,long coords
def lookup_postal_code(postal_code):
    url = "https://geocoder.ca/?postal={postal_code}&geoit=XML".format(
        postal_code=postal_code
    )
    response = requests.get(url)
    data = response.text
    longitude = data.split("<longt>")[1].split("</longt>")[0]
    latitude = data.split("<latt>")[1].split("</latt>")[0]
    return longitude, latitude




# Run the app
if __name__ == "__main__":
    app.run()
