# https://gist.github.com/snacsnoc/a54f5055c02eaa33c4b9d772dc2c8293
class ProductDataParser:
    def parse_pc_json_data(data):
        product_data = data["results"]
        for product_code in product_data:
            product_info_map = {
                "name": product_code["name"],
                "price": product_code["prices"]["price"]["value"],
                "quantity": product_code["prices"]["price"]["quantity"],
                "unit": product_code["prices"]["price"]["unit"],
                "image":product_code["imageAssets"][0]["mediumUrl"]
            }
            return product_info_map

    def parse_safeway_json_data(data):
        product_data = data["entities"]["product"]
        for product_id, product_info in product_data.items():
            product_info_map = {
                "name": product_info["name"],
                "price": product_info["price"]["current"]["amount"],
                "image": product_info["image"]['src'],
                "unit": product_info["price"]["unit"]["label"]
            }
            return product_info_map

    def parse_saveonfoods_json_data(data):
        product_data = data["products"]
        for product_code in product_data:
            product_info_map = {
                "name": product_code["name"],
                "price": product_code["priceNumeric"],
                "quantity": product_code["unitOfSize"]["size"],
                "unit": product_code["unitOfSize"]["type"],
                "image":product_code["image"]["default"]
            }
            return product_info_map
