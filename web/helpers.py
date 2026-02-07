import concurrent.futures
import json

from flask import abort, current_app

from utils.location_lookupc import LocationLookupC


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
    enabled_stores = {
        "walmart": "enable_walmart" in request_form,
        "saveon": "enable_saveon" in request_form,
        "safeway": "enable_safeway" in request_form,
        "pc": "enable_pc" in request_form,
    }

    return query, postal_code, enabled_stores


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
    enabled_stores,
    parser,
    location,
    pc_store_name,
    saveon_store_name,
    safeway_store_name,
    walmart_store_data,
    pc_store_data,
    saveon_store_data,
):
    latitude, longitude, postal_code, formatted_address = location
    pc_result = results.get("query_pc")
    saveon_result = results.get("query_saveon")
    safeway_result = results.get("query_safeway")
    walmart_result = results.get("query_walmart")

    pc_enabled = enabled_stores.get("pc")
    saveon_enabled = enabled_stores.get("saveon")
    safeway_enabled = enabled_stores.get("safeway")
    walmart_enabled = enabled_stores.get("walmart")

    # Initialize Walmart values to avoid UnboundLocalError
    # Walmart has a high chance of blocking "automated" requests
    walmart_data_parsed = []
    walmart_store_name = "Unknown Store"
    walmart_warning = None

    pc_data = []
    if pc_enabled and isinstance(pc_result, dict):
        pc_data = parser.parse_pc_json_data(pc_result) or []
    if not pc_enabled:
        pc_store_name = "Disabled"

    parsed_saveon_data = []
    if saveon_enabled:
        if not isinstance(saveon_result, Exception) and saveon_result is not None:
            if not (isinstance(saveon_result, dict) and "status" in saveon_result):
                parsed_saveon_data = (
                    parser.parse_saveonfoods_json_data(saveon_result) or []
                )
    else:
        saveon_store_name = "Disabled"

    safeway_data = None
    if safeway_enabled and "query_safeway" in results:
        if isinstance(safeway_result, dict):
            safeway_data = parser.parse_safeway_json_data(safeway_result) or []
        else:
            safeway_data = []

    walmart_store_list = []
    selected_walmart_store_id = None
    if walmart_enabled:
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
            node_id = walmart_store_entry.get(
                "nodeId", walmart_store_entry.get("id", "Unknown")
            )
            display_name = walmart_store_entry.get("displayName", "Unknown Store")
            walmart_store_name = f"{node_id} - {display_name}"
    else:
        walmart_store_name = "Disabled"

    walmart_debug = None
    if walmart_enabled and "query_walmart" in results:
        if isinstance(walmart_result, dict) and walmart_result.get("_error"):
            walmart_debug = {
                "status": walmart_result.get("_status"),
                "error": walmart_result.get("_error"),
                "body": walmart_result.get("_body"),
            }
        if not isinstance(walmart_result, Exception) and walmart_result is not None:
            walmart_data_parsed = parser.parse_walmart_json_data(walmart_result) or []

    if walmart_debug is None and isinstance(walmart_store_data, dict):
        if (
            walmart_store_data.get("status")
            or walmart_store_data.get("error")
            or walmart_store_data.get("body")
        ):
            walmart_debug = {
                "status": walmart_store_data.get("status"),
                "error": walmart_store_data.get("error"),
                "body": walmart_store_data.get("body"),
            }

    results_payload = {}
    if saveon_enabled:
        results_payload["saveon"] = parsed_saveon_data
    if pc_enabled:
        results_payload["pc"] = pc_data
    if walmart_enabled:
        results_payload["walmart"] = walmart_data_parsed
    if safeway_enabled:
        results_payload["safeway"] = safeway_data

    search_data = {
        "query": query,
        "store_name": {
            "pc": pc_store_name,
            "saveon": saveon_store_name,
            "safeway": safeway_store_name,
            "walmart": walmart_store_name,
        },
        "walmart_warning": walmart_warning,
        "walmart_debug": walmart_debug,
        "results": results_payload,
        "coords": {
            "latitude": latitude,
            "longitude": longitude,
            "postal_code": postal_code,
            "formatted_address": formatted_address,
        },
        "debug_mode": current_app.config["DEBUG"],
        "enabled_stores": enabled_stores,
        "store_locations": {
            "pc": pc_store_data.get("ResultList", []),
            "saveon": saveon_store_data.get("items", []),
            "walmart": walmart_store_list,
        },
    }
    if not any(search_data["results"].values()):
        search_data["error"] = "No results"
    if not safeway_enabled:
        search_data["store_name"]["safeway"] = "Disabled"

    return search_data


def set_store_ids(
    request_form, products_data, latitude, longitude, postal_code, enabled_stores=None
):
    enabled_stores = enabled_stores or {}
    pc_enabled = enabled_stores.get("pc")
    saveon_enabled = enabled_stores.get("saveon")
    safeway_enabled = enabled_stores.get("safeway")
    walmart_enabled = enabled_stores.get("walmart")

    d = {"ResultList": []}
    pc_store_id = None
    pc_store_name = "Disabled"
    if pc_enabled:
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

    e = {"items": []}
    saveon_store_id = None
    saveon_store_name = "Disabled"
    if saveon_enabled:
        e = products_data.search_stores_saveon(latitude, longitude)
        if "saveon-store-select" in request_form:
            saveon_store_id = request_form["saveon-store-select"]
            saveon_store_name = saveon_store_id
        else:
            saveon_store_id = e["items"][0]["retailerStoreId"] if e["items"] else False
            saveon_store_name = e["items"][0]["name"] if e["items"] else False

    safeway_store_name = "Disabled"
    if safeway_enabled:
        safeway_store_search = products_data.search_stores_safeway(
            latitude, longitude
        )
        safeway_hits = safeway_store_search.get("hits", [])
        safeway_store_id = None
        safeway_store_entry = None
        selected_safeway_id = request_form.get("safeway-store-select")
        if selected_safeway_id:
            safeway_store_entry = next(
                (
                    store
                    for store in safeway_hits
                    if str(store.get("storeNumber")) == str(selected_safeway_id)
                ),
                None,
            )
        if safeway_store_entry is None and safeway_hits:
            safeway_store_entry = safeway_hits[0]
        if safeway_store_entry:
            safeway_store_id = safeway_store_entry.get("storeNumber")
            safeway_store_name = (
                f"{safeway_store_id} - "
                f"{safeway_store_entry.get('locationName', 'Safeway')}"
            )
        else:
            safeway_store_name = "Unavailable"
        if safeway_store_id:
            products_data.set_store_safeway(safeway_store_id)

    walmart_store_data = {
        "id": None,
        "name": "Disabled",
        "payload": {"stores": []},
        "status": None,
        "error": None,
        "body": None,
    }
    if walmart_enabled:
        walmart_store_data = set_walmart_store_data(
            request_form, products_data, postal_code, latitude, longitude
        )

    return (
        pc_store_id,
        pc_store_name,
        saveon_store_id,
        saveon_store_name,
        safeway_store_name,
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
