from flask import Flask, render_template, request, redirect, abort, url_for
import concurrent.futures
import os

from line_profiler_pycharm import profile

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


def validate_request_form(request_form):
    if "query" not in request_form or "postal_code" not in request_form:
        print("ERROR: Missing params")
        abort(400, "Missing query or postal_code in request.form")

    if (
        request_form.get("query", "").strip() == ""
        or request_form.get("postal_code", "").strip() == ""
    ):
        print("ERROR: empty params")
        abort(400, "query or postal_code empty in request.form")

    query = request_form["query"]
    postal_code = request_form["postal_code"].replace(" ", "")
    enable_safeway = True if "enable_safeway" in request_form else False

    return query, postal_code, enable_safeway


def get_geo_coords(postal_code):
    if postal_code is None:
        raise Exception("Postal code is required")

    if DEBUG == "TRUE":
        longitude = "-115.69"
        latitude = "49.420"
    else:
        try:
            postal_lookup = LocationLookupC(OPENCAGE_API_KEY, cache_type="pickle")
            longitude, latitude, formatted_address = postal_lookup.lookup_coords(
                postal_code
            )
        except Exception as e:
            print(f"Error looking up postal code: {e}")
            raise

    if latitude is None:
        raise Exception("No geo coords!")

    return longitude, latitude, formatted_address


def set_walmart_store_data(request_form, products_data, postal_code):
    walmart_store_search = products_data.search_stores_walmart(postal_code)

    if "walmart-store-select" in request_form:
        walmart_store_id = request_form["walmart-store-select"]

        walmart_store_name = [
            store["displayName"]
            for store in walmart_store_search["payload"]["stores"]
            if store["id"] == walmart_store_id
        ]
    else:
        walmart_store_id = walmart_store_search["payload"]["stores"][0]["id"]
        walmart_store_name = walmart_store_search["payload"]["stores"][0]["displayName"]

    return {
        "id": str(walmart_store_id),
        "name": walmart_store_name,
        "payload": {"stores": walmart_store_search["payload"]["stores"]},
    }


@profile
def set_store_ids(request_form, products_data, latitude, longitude, postal_code):
    d = products_data.search_stores_pc(latitude, longitude, store_brand="superstore")
    if "pc-store-select" in request_form:
        pc_store_id = request_form["pc-store-select"]
        pc_store_name = pc_store_id
    else:
        try:
            value = d["ResultList"][0]["Attributes"][0]["AttributeValue"]
            # Set default store number (for whatever reason, store search can return an empty store ID)
            pc_store_id = 1517 if value == "False" else value
        except (KeyError, IndexError):
            pc_store_id = d["ResultList"][0]["Attributes"][0]["AttributeId"]  # or another default value if you prefer
        pc_store_name = d["ResultList"][0]["Name"]

    e = products_data.search_stores_saveon(latitude, longitude)
    if "saveon-store-select" in request_form:
        saveon_store_id = request_form["saveon-store-select"]
        saveon_store_name = saveon_store_id
    else:
        saveon_store_id = e["items"][0]["retailerStoreId"] if e["items"] else False
        saveon_store_name = e["items"][0]["name"] if e["items"] else False

    walmart_store_data = set_walmart_store_data(
        request_form, products_data, postal_code
    )

    return (
        pc_store_id,
        pc_store_name,
        saveon_store_id,
        saveon_store_name,
        walmart_store_data,
        d,
        e,
    )


def execute_search(functions):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_function = {executor.submit(func): func for func in functions}
        results = {}
        for future in concurrent.futures.as_completed(future_to_function):
            func = future_to_function[future]
            try:
                result = future.result()
            except Exception as exc:
                # print(f"Function {func.__name__} generated an exception: {exc}")
                results[func.__name__] = exc
            else:
                results[func.__name__] = result

    return results


def process_search_results(
    results,
    query,
    enable_safeway,
    parser,
    latitude,
    longitude,
    postal_code,
    formatted_address,
    pc_store_name,
    saveon_store_name,
    walmart_store_data,
    pc_store_data,
    saveon_store_data,
):
    a = results["query_pc"]
    c = results["query_saveon"]
    #print("results!\n\n", results)
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

    if "query_walmart" in results:
        f = results["query_walmart"]
        walmart_data_parsed = (
            parser.parse_walmart_json_data(f) if f is not None else None
        )
    else:
        walmart_data_parsed = {"none": False}

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
                "walmart": f"{walmart_store_data[0]['id']} - {walmart_store_data[0]['displayName']}",
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
                "pc": pc_store_data["ResultList"],
                "saveon": saveon_store_data["items"],
                "walmart": walmart_store_data,
            },
        }
    if enable_safeway:
        search_data["results"]["safeway"] = safeway_data
        search_data["store_name"]["safeway"] = "Safeway - GTA-MTL"

    return search_data


@app.route("/search", methods=("GET", "POST"))
def search():
    query, postal_code, enable_safeway = validate_request_form(request.form)

    products_data = SupermarketAPI(query)
    parser = ProductDataParser

    functions = [
        products_data.query_saveon,
        products_data.query_pc,
    ]

    if enable_safeway:
        functions.append(products_data.query_safeway)

    longitude, latitude, formatted_address = get_geo_coords(postal_code)
    (
        pc_store_id,
        pc_store_name,
        saveon_store_id,
        saveon_store_name,
        walmart_store_data,
        d,
        e,
    ) = set_store_ids(request.form, products_data, latitude, longitude, postal_code)

    products_data.set_store_saveon(saveon_store_id)
    products_data.set_store_pc(pc_store_id)

    # Execute Walmart search only if "walmart-store-select" is in the request form
    # if "walmart-store-select" in request.form:
    #    functions.append(products_data.query_walmart)

    # TODO: does not work when switching stores
    if "walmart-store-select" in request.form:
        walmart_store_data["id"] = request.form["walmart-store-select"]
    else:
        walmart_store_data["id"] = str(walmart_store_data["payload"]["stores"][0]["id"])

    # print(walmart_store_data["id"])
    walmart_store_data["name"] = walmart_store_data["payload"]["stores"][0][
        "displayName"
    ]

    products_data.set_store_walmart(walmart_store_data["id"])

    # Execute Walmart search
    functions.append(products_data.query_walmart)

    results = execute_search(functions)
    search_data = process_search_results(
        results,
        query,
        enable_safeway,
        parser,
        latitude,
        longitude,
        postal_code,
        formatted_address,
        pc_store_name,
        saveon_store_name,
        walmart_store_data["payload"]["stores"],
        d,
        e,
    )

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
