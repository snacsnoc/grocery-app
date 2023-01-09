from flask import Flask, render_template, request
import concurrent.futures
import requests
import os

import pickle

from product_data_parser import ProductDataParser
from supermarket import SupermarketAPI

# Create the Flask application
app = Flask(__name__)
DEBUG = os.getenv("DEBUG_MODE")
GEOCODER_API_KEY = os.getenv("GEOCODER_API_KEY")
OPENCAGE_API_KEY = os.getenv("OPENCAGE_API_KEY")

cache_dir = "cache"

if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)


# Define the route for the index page
@app.route("/")
def index():
    page_data = {"debug_mode": DEBUG}
    # Render the index.html template in the /templates directory
    return render_template("index.html", result_data=page_data)


@app.route("/search", methods=("GET", "POST"))
def search():
    print(request.form)
    if "query" not in request.form or "postal_code" not in request.form:
        raise ValueError("Missing query or postal_code in request.form")

    query = request.form["query"]
    postal_code = request.form["postal_code"]

    # Look up users postal code, convert to lat & long to search for user's local stores
    # Get each store's normalized data using ProductDataParser
    products_data = SupermarketAPI(query)
    parser = ProductDataParser

    if postal_code is None:
        raise Exception("Postal code is required")

    # If DEBUG is "TRUE", set longitude and latitude to default values
    if DEBUG == "TRUE":
        longitude = "-115.69"
        latitude = "49.420"
    else:
        # Attempt to get longitude, latitude, and formatted_address by looking up the postal code
        try:
            longitude, latitude, formatted_address = lookup_postal_code_oc(postal_code)
        except Exception as e:
            print(f"Error looking up postal code: {e}")
            raise

    # If latitude is None, raise an exception
    if latitude is None:
        raise Exception("No geo coords!")

    d = products_data.search_stores_pc(latitude, longitude, store_brand="superstore")

    # Set stores by user form selection
    if "pc-store-select" in request.form:
        pc_store_id = request.form["pc-store-select"]
        pc_store_name = pc_store_id

    else:
        pc_store_id = d["ResultList"][0]["Attributes"][0]["AttributeValue"]
        pc_store_name = d["ResultList"][0]["Name"]

    e = products_data.search_stores_saveon(latitude, longitude)

    # Check if we have Save-On stores near us
    if not e["items"]:
        saveon_store_name = False
        saveon_store_id = False
    else:
        if "saveon-store-select" in request.form:
            saveon_store_id = request.form["saveon-store-select"]
            saveon_store_name = saveon_store_id
        else:
            saveon_store_id = e["items"][0]["retailerStoreId"]
            saveon_store_name = e["items"][0]["name"]

    products_data.set_store_saveon(saveon_store_id)

    walmart_store = products_data.search_stores_walmart(postal_code)

    # Set default stores (closest store)
    products_data.set_store_pc(pc_store_id)

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

    if results["query_saveon"]["status"] == 404:
        parsed_saveon_data = "no results"
    else:
        parsed_saveon_data = parser.parse_saveonfoods_json_data(c)

    b = results["query_safeway"]
    f = results["query_walmart"]

    # Check if we have results for all stores
    # TODO: rewrite this
    if not all([a, b, c, f]):
        search_data = {
            "error": "No results",
            "coords": {"latitude": latitude, "longitude": longitude},
            "debug_mode": DEBUG,
        }
    else:
        search_data = {
            "query": query,
            "store_name": {
                "pc": pc_store_name,
                "saveon": saveon_store_name,
                "safeway": "Safeway - GTA-MTL",
                "walmart": str(walmart_store["payload"]["stores"][0]["id"])
                + " - "
                + walmart_store["payload"]["stores"][0]["displayName"],
            },
            "results": {
                "safeway": parser.parse_safeway_json_data(b),
                "saveon": parsed_saveon_data,
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
            "store_locations": {
                "pc": d["ResultList"],
                "saveon": e["items"],
                "walmart": walmart_store["payload"]["stores"],
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


def lookup_postal_code_oc(postal_code):
    """Look up the latitude and longitude for a Canadian postal code.

    Args:
        postal_code (str): A Canadian postal code.

    Returns:
        A tuple containing the latitude and longitude for the postal code, in that order.
    """
    # Check if the results are already in the cache
    cache_filename = f"cache/postal_code_{postal_code}.pkl"

    if not os.path.exists(cache_filename):
        print("Postal code cache miss")
    else:
        with open(cache_filename, "rb") as f:
            print("Postal code cache hit")
            return pickle.load(f)

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

    # Save the results to the cache
    with open(cache_filename, "wb") as f:
        pickle.dump((longitude, latitude, formatted_address), f)

    return longitude, latitude, formatted_address


# Run the app
if __name__ == "__main__":
    app.run()
