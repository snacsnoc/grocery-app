# routes.py
from flask import render_template, request, redirect, url_for
from helpers import (
    validate_request_form,
    get_geo_coords,
    execute_search,
    process_search_results,
    set_store_ids,
)
from services import SupermarketAPI, ProductDataParser


async def async_execute_search(functions, session):
    results = {}
    for func in functions:
        try:
            result = await func(session)
            results[func.__name__] = result
        except Exception as exc:
            results[func.__name__] = exc
    return results


def configure_routes(app):
    @app.route("/")
    def index():
        return render_template(
            "index.html", result_data={"debug_mode": app.config["DEBUG"]}
        )

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
            pc_store_data,
            saveon_store_data,
        ) = set_store_ids(request.form, products_data, latitude, longitude, postal_code)

        products_data.set_store_saveon(saveon_store_id)
        products_data.set_store_pc(pc_store_id)

        # Execute Walmart search only if "walmart-store-select" is in the request form
        # if "walmart-store-select" in request.form:
        #    functions.append(products_data.query_walmart)

        walmart_store_id = None
        walmart_stores = []
        if isinstance(walmart_store_data, dict):
            walmart_store_id = walmart_store_data.get("id")
            walmart_stores = walmart_store_data.get("payload", {}).get("stores", [])

        if walmart_stores and walmart_store_id not in (None, "", "Unavailable"):
            products_data.set_store_walmart(walmart_store_id)
            functions.append(products_data.query_walmart)

        results = execute_search(functions)
        location = [latitude, longitude, postal_code, formatted_address]
        search_data = process_search_results(
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
        )

        return render_template("search.html", result_data=search_data)
