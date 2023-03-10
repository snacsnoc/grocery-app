# https://gist.github.com/snacsnoc/a54f5055c02eaa33c4b9d772dc2c8293
class ProductDataParser:
    def parse_pc_json_data(data):
        product_data = data["results"]
        result = []
        for product_code in product_data:
            if product_code["imageAssets"] != None:
                image = product_code["imageAssets"][0]["smallRetinaUrl"]
            else:
                image = (
                    "https://lib.store.yahoo.net/lib/yhst-47024838256514/emoji-sad.png"
                )
            if (
                len(product_code["prices"]["comparisonPrices"]) > 0
                and product_code["prices"]["comparisonPrices"][0]["value"] is not None
            ):
                unit_price = product_code["prices"]["comparisonPrices"][0]["value"]
            else:
                unit_price = "NA"

            product_info_map = {
                "name": product_code["name"],
                "price": product_code["prices"]["price"]["value"],
                "quantity": product_code["prices"]["price"]["quantity"],
                "unit": product_code["prices"]["price"]["unit"],
                "unit_price": f"${unit_price}/100",
                "image": image,
            }

            result.append(product_info_map)
        return result

    def parse_safeway_json_data(data):
        product_data = data["entities"]["product"]
        result = []
        for product_id, product_info in product_data.items():
            product_info_map = {
                "name": product_info["name"],
                "price": product_info["price"]["current"]["amount"],
                "image": product_info["image"]["src"],
                "unit_price": "NA",
                "unit": product_info["price"]["unit"]["label"],
            }
            result.append(product_info_map)
        return result

    def parse_saveonfoods_json_data(data):
        product_data = data["products"]
        result = []
        for product_code in product_data:
            # This is very CPU expensive line of code
            unit_price = (
                product_code["priceNumeric"] / product_code["unitOfSize"]["size"]
            ) * 100
            product_info_map = {
                "name": product_code["name"],
                "price": product_code["priceNumeric"],
                "quantity": product_code["unitOfSize"]["size"],
                "unit": product_code["unitOfSize"]["type"],
                "unit_price": f"${unit_price:.2f}/100",
                "image": product_code["image"]["default"],
            }
            result.append(product_info_map)
        return result

    def parse_walmart_json_data(data):
        product_data = data["data"]["search"]["searchResult"]["itemStacks"][0][
            "itemsV2"
        ]
        result = []
        for product_code in product_data:
            if product_code["priceInfo"]["unitPrice"] != None:
                quantity = product_code["priceInfo"]["unitPrice"]["priceString"]
            else:
                quantity = "NA"

            if product_code["priceInfo"]["currentPrice"] != None:
                price = product_code["priceInfo"]["currentPrice"]["price"]
            else:
                price = "NA"
            image = "https://lib.store.yahoo.net/lib/yhst-47024838256514/emoji-sad.png"
            if 'allImages' in product_code['imageInfo']:
                if product_code['imageInfo']['allImages'] and product_code['imageInfo']['allImages'][0]:
                    image = product_code['imageInfo']['allImages'][0]['url']

            product_info_map = {
                "name": product_code["name"],
                "price": price,
                "quantity": "NA-",
                "unit": product_code["salesUnitType"],
                "unit_price": quantity,
                "image": image,
            }
            result.append(product_info_map)
        return result
