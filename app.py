from flask import Flask, render_template, request, redirect, abort, url_for
import concurrent.futures
import os


from product_data_parser import ProductDataParser
from supermarket import SupermarketAPI
from location_lookupc import LocationLookupC

# Create the Flask application
app = Flask(__name__)
DEBUG = os.getenv("DEBUG_MODE")
OPENCAGE_API_KEY = os.getenv("OPENCAGE_API_KEY")
MEMCACHED_SERVER = os.getenv("MEMCACHED_SERVER")

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
        print("ERROR")
        abort(400, "Missing query or postal_code in request.form")

    if (
        request.form.get("query", "").strip() == ""
        or request.form.get("postal_code", "").strip() == ""
    ):
        print("ERROR")
        abort(400, "query or postal_code empty in request.form")

    query = request.form["query"]
    postal_code = request.form["postal_code"].replace(" ", "")

    enable_safeway = True if "enable_safeway" in request.form else False

    # Look up users postal code, convert to lat & long to search for user's local stores
    # Get each store's normalized data using ProductDataParser
    products_data = SupermarketAPI(query)
    parser = ProductDataParser

    # Set up a list of functions to send requests to
    functions = [
        products_data.query_saveon,
        products_data.query_pc,
    ]

    # Add safeway to search if user selected
    if enable_safeway:
        functions.append(products_data.query_safeway)

    if postal_code is None:
        raise Exception("Postal code is required")

    # If DEBUG is "TRUE", set longitude and latitude to default values
    if DEBUG == "TRUE":
        longitude = "-115.69"
        latitude = "49.420"
    else:
        # Attempt to get long, lat, and formatted_address by looking up the postal code
        try:
            postal_lookup = LocationLookupC(OPENCAGE_API_KEY, cache_type="pickle")
            longitude, latitude, formatted_address = postal_lookup.lookup_coords(postal_code)
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

    # Default distance for SaveOn is 50km, seems generous enough
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

    walmart_store_data = {}
    # Use this for store list on search result page
    walmart_store_search = products_data.search_stores_walmart(postal_code)

    # If the store search fails, set default data
    # Since setting the store currently uses lat/long + postal code,
    # we can assume when the store search fails, there will be no nearest stores
    # so we do not bother to query Walmart's product search API
    if not walmart_store_search["payload"]["stores"]:
        walmart_store_data["id"] = walmart_store_data["name"] = 0
    else:
        walmart_store_data["id"] = str(
            walmart_store_search["payload"]["stores"][0]["id"]
        )
        walmart_store_data["name"] = walmart_store_search["payload"]["stores"][0][
            "displayName"
        ]

        # Walmart store is set by lat/long not store_id (yet)
        products_data.set_store_walmart(latitude, longitude, postal_code)

        # Execute W almart search
        functions.append(products_data.query_walmart)

    # Set default stores (closest store)
    products_data.set_store_pc(pc_store_id)

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

    # Depending on the user's location, there can be no stores around
    if "status" in results["query_saveon"]:
        parsed_saveon_data = "no results"
    else:
        parsed_saveon_data = parser.parse_saveonfoods_json_data(c)

    if enable_safeway:
        if results["query_safeway"]["entities"] is None:
            safeway_data = parser.parse_safeway_json_data(results["query_safeway"])
        else:
            safeway_data = "no result"
    else:
        safeway_data = None

    # Check if we queried walmart, otherwise return null data to display
    if "query_walmart" in results:
        f = results["query_walmart"]
        # Check if we have Walmart results
        walmart_data_parsed = (
            parser.parse_walmart_json_data(f) if f is not None else None
        )
    else:
        walmart_data_parsed = {"none": False}

    # Check if we have results for all stores
    # TODO: rewrite this
    if not all([a, c]):
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
                "walmart": str(walmart_store_data["id"])
                + " - "
                + str(walmart_store_data["name"]),
            },
            "results": {
                "saveon": parsed_saveon_data,
                "pc": parser.parse_pc_json_data(a),
                "walmart": walmart_data_parsed,
            },
            "coords": {
                "latitude": latitude,
                "longitude": longitude,
                "postal_code": postal_code,
                "formatted_address": formatted_address,
            },
            "debug_mode": DEBUG,
            "enable_safeway": enable_safeway,
            "store_locations": {
                "pc": d[
                    "ResultList"
                ],  # TODO: check for false store IDs, prevents changing PC stores in search.html
                "saveon": e["items"],
                "walmart": walmart_store_search["payload"]["stores"],
            },
        }

    if enable_safeway:
        search_data["results"]["safeway"] = safeway_data
        search_data["store_name"]["safeway"] = "Safeway - GTA-MTL"

    return render_template("search.html", result_data=search_data)



@app.errorhandler(400)
def bad_request(error):
    # Redirect to home for now
    # TODO: write the rest of this thing
    return redirect(url_for("index"))


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(Exception)
def handle_exception(e):
    # Log the error
    app.logger.exception(e)
    # Render an error template
    return render_template("error.html"), 500


# Run the app
if __name__ == "__main__":
    app.run()
