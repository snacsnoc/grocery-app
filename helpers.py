# helpers.py
import concurrent.futures

from flask import abort, current_app

from location_lookupc import LocationLookupC


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

    if current_app.config["DEBUG"] == "TRUE":
        longitude = "-115.69"
        latitude = "49.420"
    else:
        try:
            postal_lookup = LocationLookupC(
                current_app.config["OPENCAGE_API_KEY"], cache_type="pickle"
            )
            longitude, latitude, formatted_address = postal_lookup.lookup_coords(
                postal_code
            )
        except Exception as e:
            print(f"Error looking up postal code: {e}")
            raise

    if latitude is None:
        raise Exception("No geo coords!")

    return longitude, latitude, formatted_address


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
    location,
    pc_store_name,
    saveon_store_name,
    walmart_store_data,
    pc_store_data,
    saveon_store_data,
):
    latitude, longitude, postal_code, formatted_address = location
    a = results["query_pc"]
    c = results["query_saveon"]

    if "status" in results["query_saveon"]:
        parsed_saveon_data = "no results"
    else:
        parsed_saveon_data = parser.parse_saveonfoods_json_data(c)

    if enable_safeway:
        if results["query_safeway"]["entities"] is not None:
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
        if isinstance(walmart_store_data, list) and walmart_store_data:
            walmart_store_entry = walmart_store_data[0]
            walmart_store_name = f"{walmart_store_entry.get('nodeId', 'Unknown')} - {walmart_store_entry.get('displayName', 'Unknown Store')}"
        else:
            walmart_store_name = "Unavailable"
    else:
        walmart_data_parsed = {"none": False}

    if not all([a, c]):
        search_data = {
            "error": "No results",
            "coords": {"latitude": latitude, "longitude": longitude},
            "debug_mode": current_app.config["DEBUG"],
        }
    else:
        search_data = {
            "query": query,
            "store_name": {
                "pc": pc_store_name,
                "saveon": saveon_store_name,
                "walmart": walmart_store_name,
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
            "debug_mode": current_app.config["DEBUG"],
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
            pc_store_id = d["ResultList"][0]["Attributes"][0][
                "AttributeId"
            ]  # or another default value if you prefer
        pc_store_name = d["ResultList"][0]["Name"]

    e = products_data.search_stores_saveon(latitude, longitude)
    if "saveon-store-select" in request_form:
        saveon_store_id = request_form["saveon-store-select"]
        saveon_store_name = saveon_store_id
    else:
        saveon_store_id = e["items"][0]["retailerStoreId"] if e["items"] else False
        saveon_store_name = e["items"][0]["name"] if e["items"] else False
    try:
        walmart_store_data = set_walmart_store_data(
            request_form, products_data, postal_code
        )
    except Exception as err:
        walmart_store_data = {"id": None, "name": "Unavailable", "payload": {}}

    # walmart_store_data = set_walmart_store_data(
    #     request_form, products_data, postal_code
    # )

    return (
        pc_store_id,
        pc_store_name,
        saveon_store_id,
        saveon_store_name,
        walmart_store_data,
        d,
        e,
    )


def set_walmart_store_data(request_form, products_data, postal_code):

    walmart_store_search = products_data.search_stores_walmart(postal_code)

    if not walmart_store_search or "data" not in walmart_store_search:
        raise ValueError("Invalid Walmart store search response")

    location_data = walmart_store_search["data"].get("location", {})
    pickup_node = location_data.get("pickupNode")

    if not pickup_node:
        raise ValueError("No pickup nodes found in the Walmart store search response")

    if isinstance(pickup_node, dict):
        pickup_node = [pickup_node]

    # Check if a store is selected in the form
    if "walmart-store-select" in request_form:
        walmart_store_id = request_form["walmart-store-select"]

        # Find the store by ID in the list of pickup nodes
        walmart_store_name = next(
            (
                store["displayName"]
                for store in pickup_node
                if store["nodeId"] == walmart_store_id
            ),
            "Unknown Store",
        )
    else:
        # Default to the first pickup node
        walmart_store_id = pickup_node[0]["nodeId"]
        walmart_store_name = pickup_node[0]["displayName"]

    return {
        "id": str(walmart_store_id),
        "name": walmart_store_name,
        "payload": {"stores": pickup_node},
    }
