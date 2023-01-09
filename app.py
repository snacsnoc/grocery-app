from flask import Flask, render_template, request
import concurrent.futures
import requests
import os

from product_data_parser import ProductDataParser
from supermarket import SupermarketAPI

# Create the Flask application
app = Flask(__name__)
DEBUG = os.getenv("DEBUG_MODE")
GEOCODER_API_KEY = os.getenv("GEOCODER_API_KEY")
OPENCAGE_API_KEY = os.getenv("OPENCAGE_API_KEY")

# Define the route for the index page
@app.route("/")
def index():
    page_data = {"debug_mode": DEBUG}
    # Render the index.html template in the /templates directory
    return render_template("index.html", result_data=page_data)


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

        if DEBUG == "TRUE":
            longitude = "-115.69"
            latitude = "49.420"
        else:
            longitude, latitude, formatted_address = lookup_postal_code_oc(postal_code)

        if latitude is None:
            raise Exception("No geo coords!")

        d = products_data.search_stores_pc(
            latitude, longitude, store_brand="superstore"
        )
        e = products_data.search_stores_saveon(latitude, longitude)

        pc_store_id = d["ResultList"][0]["Attributes"][0]["AttributeValue"]
        saveon_store_id = e["items"][0]["retailerStoreId"]
        walmart_store = products_data.search_stores_walmart(postal_code)

        # Set default stores (closest store)
        products_data.set_store_pc(pc_store_id)
        products_data.set_store_saveon(saveon_store_id)
        products_data.set_store_walmart(latitude, longitude, postal_code)

        # Set up a list of functions to send requests to
        functions = [
            products_data.query_saveon,
            products_data.query_pc,
            products_data.query_safeway,
            products_data.query_walmart,
        ]

        # Use a ThreadPoolExecutor to send the requests in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Start the load operations and mark each future with its function
            future_to_function = {executor.submit(func): func for func in functions}
            results = {}
            for future in concurrent.futures.as_completed(future_to_function):
                func = future_to_function[future]
                try:
                    result = future.result()
                except Exception as exc:
                    print(f"Function {func.__name__} generated an exception: {exc}")
                    results[func.__name__] = exc
                else:
                    # print(f"Function {func.__name__} returned result: {result}")
                    results[func.__name__] = result

        a = results["query_pc"]
        c = results["query_saveon"]
        b = results["query_safeway"]
        f = results["query_walmart"]

        # Check if we have results for all stores
        # TODO: rewrite this
        if all([a, b, c, f]):

            search_data = {
                "store_name": {
                    "pc": d["ResultList"][0]["Name"],
                    "saveon": e["items"][0]["name"],
                    "safeway": "safewaySTORENAME",
                    "walmart": str(walmart_store["payload"]["stores"][0]["id"])
                    + " - "
                    + walmart_store["payload"]["stores"][0]["displayName"],
                },
                "results": {
                    "safeway": parser.parse_safeway_json_data(b),
                    "saveon": parser.parse_saveonfoods_json_data(c),
                    "pc": parser.parse_pc_json_data(a),
                    "walmart": parser.parse_walmart_json_data(f),
                },
                "coords": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "postal_code": postal_code,
                    "formatted_address": formatted_address,
                },
                "debug_mode": DEBUG,
            }
        else:
            search_data = {
                "error": "No results",
                "coords": {"latitude": latitude, "longitude": longitude},
                "debug_mode": DEBUG,
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


def lookup_postal_code_oc(postal_code):
    """Look up the latitude and longitude for a Canadian postal code.

    Args:
        postal_code (str): A Canadian postal code.

    Returns:
        A tuple containing the latitude and longitude for the postal code, in that order.
    """
    # Use the OpenCage Geocoder API to look up the latitude and longitude
    api_key = OPENCAGE_API_KEY
    api_url = (
        f"https://api.opencagedata.com/geocode/v1/json?q={postal_code}&key={api_key}"
    )
    response = requests.get(api_url)
    data = response.json()

    # Extract the latitude and longitude from the API response
    latitude = data["results"][0]["geometry"]["lat"]
    longitude = data["results"][0]["geometry"]["lng"]
    formatted_address = data["results"][0]["formatted"]

    return longitude, latitude, formatted_address


# Run the app
if __name__ == "__main__":
    app.run()
