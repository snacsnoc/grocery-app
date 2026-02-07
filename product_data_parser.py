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
        result = []
        results = data.get("results", [])
        if not results:
            return result

        products = results[0].get("hits", [])
        for product_info in products:
            name = product_info.get("name", "NA")
            price = product_info.get("price", "0")

            try:
                price_float = float(price)
                price_string = f"${price_float:.2f}"
            except (TypeError, ValueError):
                price_float = None
                price_string = "NA"

            item_amount_value = product_info.get("itemAmountValue")
            item_amount_unit = product_info.get("itemAmountUnit")
            weight_in_grams = None
            if item_amount_value is not None and item_amount_unit:
                try:
                    amount_value = float(item_amount_value)
                    if str(item_amount_unit).upper() == "G":
                        weight_in_grams = int(amount_value)
                    elif str(item_amount_unit).upper() == "KG":
                        weight_in_grams = int(amount_value * 1000)
                except (TypeError, ValueError):
                    weight_in_grams = None

            if weight_in_grams is None:
                weight_str = product_info.get("weight", "")
                weight_match = re.search(
                    r"(\d+(?:\.\d+)?)\s*(KG|G)",
                    weight_str,
                    re.IGNORECASE,
                )
                if weight_match:
                    value = float(weight_match.group(1))
                    unit = weight_match.group(2).upper()
                    weight_in_grams = int(value * 1000) if unit == "KG" else int(value)

            if weight_in_grams is None:
                name_match = re.search(r"(\d+)\s*g", name, re.IGNORECASE)
                weight_in_grams = int(name_match.group(1)) if name_match else None

            if weight_in_grams and price_float is not None:
                unit_price = (price_float / weight_in_grams) * 100
                unit_price_string = f"${unit_price:.2f}/100g"
            else:
                unit_price_string = "NA"

            images = product_info.get("images", [])
            image = (
                images[0]
                if isinstance(images, list) and images
                else ProductDataParser.get_image({})
            )

            product_info_map = {
                "name": name,
                "price": price_string,
                "image": image,
                "quantity": weight_in_grams or item_amount_value,
                "unit_price": unit_price_string,
                "unit": item_amount_unit or product_info.get("uom", "NA"),
            }
            result.append(product_info_map)

        return result

    @staticmethod
    def parse_saveonfoods_json_data(data):
        product_data = data.get("products", [])

        def normalize_price(value):
            if value is None:
                return "NA"
            if isinstance(value, (int, float)):
                return value
            value_str = str(value).strip()
            if not value_str:
                return "NA"
            value_str = value_str.replace("$", "").replace(",", "")
            return value_str or "NA"

        return [
            {
                "name": product.get("name", "NA"),
                "price": normalize_price(product.get("priceNumeric")),
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
