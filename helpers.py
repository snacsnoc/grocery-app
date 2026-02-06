import concurrent.futures
import json

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
        formatted_address = "Debug Address"
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
    pc_result = results.get("query_pc")
    saveon_result = results.get("query_saveon")

    # Initialize Walmart values to avoid UnboundLocalError
    # Walmart has a high chance of blocking "automated" requests
    walmart_data_parsed = []
    walmart_store_name = "Unknown Store"
    walmart_warning = None

    walmart_store_list = []
    selected_walmart_store_id = None
    if isinstance(walmart_store_data, list):
        walmart_store_list = walmart_store_data
    elif isinstance(walmart_store_data, dict):
        walmart_store_list = walmart_store_data.get("payload", {}).get("stores", [])
        selected_walmart_store_id = walmart_store_data.get("id")

    if walmart_store_list:
        walmart_store_entry = None
        if selected_walmart_store_id not in (None, "", "Unavailable"):
            selected_walmart_store_id = str(selected_walmart_store_id)
            walmart_store_entry = next(
                (
                    store
                    for store in walmart_store_list
                    if str(store.get("nodeId", store.get("id")))
                    == selected_walmart_store_id
                ),
                None,
            )
        if walmart_store_entry is None:
            walmart_store_entry = walmart_store_list[0]
        walmart_store_name = f"{walmart_store_entry.get('nodeId', walmart_store_entry.get('id', 'Unknown'))} - {walmart_store_entry.get('displayName', 'Unknown Store')}"

    pc_data = []
    if isinstance(pc_result, dict):
        pc_data = parser.parse_pc_json_data(pc_result) or []

    if isinstance(saveon_result, Exception) or saveon_result is None:
        parsed_saveon_data = []
    elif isinstance(saveon_result, dict) and "status" in saveon_result:
        parsed_saveon_data = []
    else:
        parsed_saveon_data = parser.parse_saveonfoods_json_data(saveon_result) or []

    if enable_safeway and "query_safeway" in results:
        safeway_result = results["query_safeway"]
        if isinstance(safeway_result, Exception):
            safeway_data = []
        elif (
            isinstance(safeway_result, dict)
            and safeway_result.get("entities") is not None
        ):
            safeway_data = parser.parse_safeway_json_data(safeway_result) or []
        else:
            safeway_data = []
    else:
        safeway_data = None

    walmart_debug = None
    if "query_walmart" in results:
        f = results["query_walmart"]
        if isinstance(f, Exception) or f is None:
            pass
        else:
            if isinstance(f, dict) and f.get("_error"):
                walmart_debug = {
                    "status": f.get("_status"),
                    "error": f.get("_error"),
                    "body": f.get("_body"),
                }

            walmart_data_parsed = parser.parse_walmart_json_data(f) or []

    search_data = {
        "query": query,
        "store_name": {
            "pc": pc_store_name,
            "saveon": saveon_store_name,
            "walmart": walmart_store_name,
        },
        "walmart_warning": walmart_warning,
        "walmart_debug": (
            walmart_debug
            or {
                "status": walmart_store_data.get("status"),
                "error": walmart_store_data.get("error"),
                "body": walmart_store_data.get("body"),
            }
            if isinstance(walmart_store_data, dict)
            and (
                walmart_store_data.get("status")
                or walmart_store_data.get("error")
                or walmart_store_data.get("body")
            )
            else None
        ),
        "results": {
            "saveon": parsed_saveon_data,
            "pc": pc_data,
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
            "pc": pc_store_data.get("ResultList", []),
            "saveon": saveon_store_data.get("items", []),
            "walmart": walmart_store_list,
        },
    }
    if not any(search_data["results"].values()):
        search_data["error"] = "No results"
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

    walmart_store_data = set_walmart_store_data(
        request_form, products_data, postal_code, latitude, longitude
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


def set_walmart_store_data(
    request_form, products_data, postal_code, latitude=None, longitude=None
):

    walmart_store_search = products_data.search_stores_walmart(
        postal_code, latitude, longitude
    )
    if not walmart_store_search:
        return {
            "id": None,
            "name": "Unavailable",
            "payload": {"stores": []},
            "status": None,
            "error": "No response from Walmart store lookup",
        }

    if isinstance(walmart_store_search, dict) and walmart_store_search.get("_error"):
        return {
            "id": None,
            "name": "Unavailable",
            "payload": {"stores": []},
            "status": walmart_store_search.get("_status"),
            "error": f"Walmart store lookup failed ({walmart_store_search.get('_error')})",
            "body": walmart_store_search.get("_body"),
        }

    if "data" not in walmart_store_search:
        return {
            "id": None,
            "name": "Unavailable",
            "payload": {"stores": []},
            "status": None,
            "error": "Invalid Walmart store search response",
        }

    data = walmart_store_search.get("data", {})
    if not data:
        return {
            "id": None,
            "name": "Unavailable",
            "payload": {"stores": []},
            "status": None,
            "error": "No data in Walmart store search response",
        }

    nearByNodes = data.get("nearByNodes", {})
    if isinstance(nearByNodes, dict):
        nodes = nearByNodes.get("nodes")
    else:
        nodes = None

    if not nodes:
        nodes = data.get("location", {}).get("pickupNode")

    if not nodes:
        return {
            "id": None,
            "name": "Unavailable",
            "payload": {"stores": []},
            "status": None,
            "error": "No Walmart pickup nodes found",
        }

    if isinstance(nodes, dict):
        nodes = [nodes]

    for n in nodes:
        n.setdefault("nodeId", n.get("id"))

    # Check if a store is selected in the form
    selected_id = request_form.get("walmart-store-select", nodes[0]["nodeId"])

    store = next((n for n in nodes if n["nodeId"] == selected_id), nodes[0])

    return {
        "id": str(store["nodeId"]),
        "name": store.get("displayName", "Unknown Store"),
        "payload": {"stores": nodes},
    }
