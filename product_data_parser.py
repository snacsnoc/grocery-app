# https://gist.github.com/snacsnoc/a54f5055c02eaa33c4b9d772dc2c8293
import re


class ProductDataParser:
    @staticmethod
    def get_image(
        product,
        default_image="https://upload.wikimedia.org/wikipedia/commons/6/67/056-crying-face.svg",
    ):
        # New PC tiles
        if product.get("productImage"):
            img = product["productImage"][0]
            return (
                img.get("smallUrl")
                or img.get("thumbnailUrl")
                or img.get("imageUrl")
                or default_image
            )

        # Walmart
        if product.get("imageAssets"):
            return product["imageAssets"][0].get("smallRetinaUrl", default_image)

        # Safeway
        if product.get("image"):
            return product["image"].get("src", default_image)

        return default_image

    @staticmethod
    def parse_pc_json_data(data):

        layout = data.get("layout") or {}
        sections = layout.get("sections") or {}
        main_col = sections.get("mainContentCollection") or {}
        comps = main_col.get("components") or []

        tiles = [t for c in comps for t in c.get("data", {}).get("productTiles", [])]

        def split_pkg(s: str):
            # "700 g, $1.26/100g" → ("700 g", "$1.26/100g")
            if not s:
                return "NA", "NA"
            left, *right = [p.strip() for p in s.split(",", 1)]
            return left, (right[0] if right else "NA")

        results = []
        for t in tiles:
            qty, unit_price = split_pkg(t.get("packageSizing", ""))

            results.append(
                {
                    "name": t.get("title", "NA"),
                    "price": t.get("pricing", {}).get("price", "NA"),
                    "quantity": qty,
                    "unit": t.get("pricingUnits", {}).get("unit", "NA"),
                    "unit_price": unit_price,
                    "image": ProductDataParser.get_image(t),
                }
            )

        return results

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
                "unit_of_measure": product.get("unitOfMeasure", {}).get("type", "NA"),
                "unit_price": (
                    product.get("pricePerUnit", "NA")
                    if product.get("pricePerUnit")
                    else f"${(product.get('priceNumeric', 0) / max(product.get('unitOfMeasure', {}).get('size', 1), 1)):.2f}/100"
                ),
                "image": product.get("image", {}).get(
                    "default", ProductDataParser.get_image({})
                ),
                "made_in_canada": product.get("attributes", {}).get(
                    "made in Canada", False
                ),
                "product_of_canada": product.get("attributes", {}).get(
                    "product of Canada", False
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

            image_info = product_code.get("imageInfo", {})
            thumbnail_url = image_info.get("thumbnailUrl")
            all_images = image_info.get("allImages", [])
            image = None
            if thumbnail_url:
                image = thumbnail_url
            elif all_images and "url" in all_images[0]:
                image = all_images[0].get("url")
            else:
                image = "https://upload.wikimedia.org/wikipedia/commons/6/67/056-crying-face.svg"

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
