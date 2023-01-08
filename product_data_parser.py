# https://gist.github.com/snacsnoc/a54f5055c02eaa33c4b9d772dc2c8293
class ProductDataParser:
    def parse_pc_json_data(data):
        product_data = data["results"]
        result = []
        for product_code in product_data:
            product_info_map = {
                "name": product_code["name"],
                "price": product_code["prices"]["price"]["value"],
                "quantity": product_code["prices"]["price"]["quantity"],
                "unit": product_code["prices"]["price"]["unit"],
                "image":product_code["imageAssets"][0]["mediumUrl"]
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
                "image": product_info["image"]['src'],
                #"size": product_info["size"]["value"],
                "unit": product_info["price"]["unit"]["label"]
            }
            result.append(product_info_map)
        return result
    def parse_saveonfoods_json_data(data):
        product_data = data["products"]
        result = []
        for product_code in product_data:
            product_info_map = {
                "name": product_code["name"],
                "price": product_code["priceNumeric"],
                "quantity": product_code["unitOfSize"]["size"],
                "unit": product_code["unitOfSize"]["type"],
                "image": product_code["image"]["default"]
            }
            result.append(product_info_map)
        return result

    def parse_walmart_json_data(data):
        product_data = data['data']['search']['searchResult']['itemStacks'][0]['itemsV2']
        result = []
        for product_code in product_data:
            product_info_map = {
                "name": product_code["name"],
                "price": product_code["priceInfo"]["currentPrice"]["price"],
                "quantity": product_code["priceInfo"]["unitPrice"]["priceString"],
                "unit": product_code["salesUnitType"],
                "image": product_code["imageInfo"]["allImages"][0]['url']
            }
            result.append(product_info_map)
        return result