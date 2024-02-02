# https://gist.github.com/snacsnoc/a54f5055c02eaa33c4b9d772dc2c8293
import re


class ProductDataParser:
    @staticmethod
    def get_image(
        product,
        default_image="https://lib.store.yahoo.net/lib/yhst-47024838256514/emoji-sad.png",
    ):
        if product.get("imageAssets"):
            return product["imageAssets"][0].get("smallRetinaUrl", default_image)
        return default_image

    @staticmethod
    def parse_pc_json_data(data):
        product_data = data.get("results", [])
        return [
            {
                "name": product.get("name", "NA"),
                "price": product.get("prices", {}).get("price", {}).get("value", "NA"),
                "quantity": product.get("packageSize", "NA"),
                "unit": product.get("prices", {}).get("price", {}).get("unit", "NA"),
                "unit_price": f"${product.get('prices', {}).get('comparisonPrices', [{}])[0].get('value', 'NA')}/100",
                "image": ProductDataParser.get_image(product),
            }
            for product in product_data
        ]

    @staticmethod
    def parse_safeway_json_data(data):
        product_data = data.get("entities", {}).get("product", {})
        result = []
        for product_id, product_info in product_data.items():
            name = product_info.get("name", "NA")
            price_dict = product_info.get("price", {}).get("current", {})
            price = price_dict.get("amount", "0")

            # Convert price to float and format as a string
            try:
                price_float = float(price)
                price_string = f"${price_float:.2f}"
            except ValueError:
                price_string = "NA"

            # Extract weight in grams from the product name
            weight_match = re.search(r"(\d+)\s*g", name, re.IGNORECASE)
            weight_in_grams = int(weight_match.group(1)) if weight_match else None

            # Calculate unit price per 100 grams
            if weight_in_grams:
                unit_price = (price_float / weight_in_grams) * 100
                unit_price_string = f"${unit_price:.2f}/100g"
            else:
                unit_price_string = "NA"

            image = product_info.get("image", {}).get(
                "src", ProductDataParser.get_image({})
            )

            product_info_map = {
                "name": name,
                "price": price_string,
                "image": image,
                "quantity": weight_in_grams,
                "unit_price": unit_price_string,
                "unit": product_info.get("price", {})
                .get("unit", {})
                .get("label", "NA"),
            }
            result.append(product_info_map)

        return result

    @staticmethod
    def parse_saveonfoods_json_data(data):
        product_data = data.get("products", [])
        return [
            {
                "name": product.get("name", "NA"),
                "price": product.get("priceNumeric", "NA"),
                "quantity": product.get("unitOfSize", {}).get("size", "NA"),
                "unit": product.get("unitOfSize", {}).get("type", "NA"),
                "unit_price": f"${(product.get('priceNumeric', 0) / product.get('unitOfSize', {}).get('size', 1)) * 100:.2f}/100",
                "image": product.get("image", {}).get(
                    "default", ProductDataParser.get_image({})
                ),
            }
            for product in product_data
        ]

    @staticmethod
    def parse_walmart_json_data(data):
        product_data = (
            data.get("data", {})
            .get("search", {})
            .get("searchResult", {})
            .get("itemStacks", [{}])[0]
            .get("itemsV2", [])
        )
        result = []
        for product_code in product_data:
            product_name = product_code.get("name")
            # Skip products with no name
            if not product_name:
                continue
            priceInfo = product_code.get("priceInfo", {})

            # listPrice = priceInfo.get("listPrice")
            # quantity = listPrice.get("priceString", "NA") if listPrice else "NA"

            current_price_dict = priceInfo.get("currentPrice")

            if current_price_dict and "price" in current_price_dict:
                price = float(current_price_dict["price"])
                price_string = f"${price:.2f}"
            else:
                price = 0
                price_string = "NA"

            # Extracting weight in grams from the product name
            weight_match = re.search(
                r"(\d+)\s*g", product_code.get("name", ""), re.IGNORECASE
            )
            # Default to 100g if not found
            weight_in_grams = int(weight_match.group(1)) if weight_match else 100

            # Calculating unit price
            unit_price = (price / weight_in_grams) * 100 if weight_in_grams else "NA"
            unit_price_string = (
                f"${unit_price:.2f}/100g" if unit_price != "NA" else "NA"
            )

            image = "https://lib.store.yahoo.net/lib/yhst-47024838256514/emoji-sad.png"
            allImages = product_code.get("imageInfo", {}).get("allImages")
            if allImages and allImages[0]:
                image = allImages[0].get("url", image)

            product_info_map = {
                "name": product_name,
                "price": price_string,
                "quantity": weight_in_grams,
                "unit": product_code.get("salesUnitType", "NA"),
                "unit_price": unit_price_string,
                "image": image,
            }
            result.append(product_info_map)
        return result
