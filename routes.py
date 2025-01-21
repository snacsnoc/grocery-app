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

import asyncio
from aiohttp import ClientSession


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

    @app.route("/asearch", methods=("GET", "POST"))
    async def asearch():
        query, postal_code, enable_safeway = validate_request_form(request.form)

        products_data = SupermarketAPI(query)
        parser = ProductDataParser()

        async with ClientSession() as session:
            functions = [
                lambda: products_data.query_saveon(session),
                lambda: products_data.query_pc(session),
            ]

            if enable_safeway:
                functions.append(lambda: products_data.query_safeway(session))

            longitude, latitude, formatted_address = get_geo_coords(postal_code)
            (
                pc_store_id,
                pc_store_name,
                saveon_store_id,
                saveon_store_name,
                walmart_store_data,
                d,
                e,
            ) = set_store_ids(
                request.form, products_data, latitude, longitude, postal_code
            )

            products_data.set_store_saveon(saveon_store_id)
            products_data.set_store_pc(pc_store_id)

            if "walmart-store-select" in request.form:
                walmart_store_data["id"] = request.form["walmart-store-select"]
            else:
                walmart_store_data["id"] = str(
                    walmart_store_data["payload"]["stores"][0]["id"]
                )

            walmart_store_data["name"] = walmart_store_data["payload"]["stores"][0][
                "displayName"
            ]

            products_data.set_store_walmart(walmart_store_data["id"])
            functions.append(lambda: products_data.query_walmart(session))

            results = await async_execute_search(functions, session)
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
            walmart_store_data["id"] = str(
                walmart_store_data["payload"]["stores"][0]["nodeId"]
            )

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
