# https://gist.github.com/snacsnoc/a54f5055c02eaa33c4b9d772dc2c8293
import re


class ProductDataParser:
    @staticmethod
    def normalize_unit(unit):
        if unit is None:
            return "NA"
        unit_str = str(unit).strip().lower()
        if not unit_str:
            return "NA"
        mapping = {
            "g": "g",
            "gram": "g",
            "grams": "g",
            "kg": "kg",
            "kilogram": "kg",
            "kilograms": "kg",
            "ml": "ml",
            "milliliter": "ml",
            "milliliters": "ml",
            "l": "l",
            "liter": "l",
            "liters": "l",
            "litre": "l",
            "litres": "l",
            "ea": "ea",
            "each": "ea",
            "count": "ea",
            "ct": "ea",
            "unit": "ea",
            "units": "ea",
            "lb": "lb",
            "lbs": "lb",
            "pound": "lb",
            "pounds": "lb",
            "oz": "oz",
            "ounce": "oz",
            "ounces": "oz",
        }
        return mapping.get(unit_str, unit_str)

    @staticmethod
    def normalize_quantity_unit(quantity, unit):
        unit_norm = ProductDataParser.normalize_unit(unit)
        if unit_norm in ("kg", "l"):
            try:
                quantity_value = float(quantity)
            except (TypeError, ValueError):
                return quantity, unit_norm
            if unit_norm == "kg":
                return quantity_value * 1000, "g"
            return quantity_value * 1000, "ml"
        return quantity, unit_norm

    @staticmethod
    def _extract_quantity_unit_from_text(text):
        if not text:
            return None, None
        match = re.search(r"(\d+(?:\.\d+)?)\s*(kg|g|ml|l)\b", text, re.IGNORECASE)
        if not match:
            return None, None
        quantity = match.group(1)
        unit = match.group(2)
        return ProductDataParser.normalize_quantity_unit(quantity, unit)

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
            unit_raw = item_amount_unit or product_info.get("uom")
            quantity = item_amount_value

            fallback_quantity, fallback_unit = ProductDataParser._extract_quantity_unit_from_text(
                product_info.get("weight", "")
            )
            if fallback_quantity is None:
                fallback_quantity, fallback_unit = (
                    ProductDataParser._extract_quantity_unit_from_text(name)
                )
            if quantity is None and fallback_quantity is not None:
                quantity = fallback_quantity
                unit_raw = unit_raw or fallback_unit
            elif unit_raw is None and fallback_unit is not None:
                unit_raw = fallback_unit

            quantity, unit = ProductDataParser.normalize_quantity_unit(
                quantity, unit_raw
            )

            unit_price_string = "NA"
            if price_float is not None:
                try:
                    quantity_value = float(quantity)
                except (TypeError, ValueError):
                    quantity_value = None
                if quantity_value and unit in ("g", "ml"):
                    unit_price = (price_float / quantity_value) * 100
                    suffix = "100g" if unit == "g" else "100ml"
                    unit_price_string = f"${unit_price:.2f}/{suffix}"

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
                "quantity": quantity,
                "unit_price": unit_price_string,
                "unit": unit,
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

        results = []
        for product in product_data:
            unit_of_size = product.get("unitOfSize", {}) or {}
            unit_of_measure = product.get("unitOfMeasure", {}) or {}
            raw_quantity = unit_of_size.get("size")
            raw_unit = unit_of_size.get("type") or unit_of_measure.get("type")
            quantity, unit = ProductDataParser.normalize_quantity_unit(
                raw_quantity, raw_unit
            )

            results.append(
                {
                    "name": product.get("name", "NA"),
                    "price": normalize_price(product.get("priceNumeric")),
                    "quantity": quantity,
                    "unit": unit,
                    "unit_of_measure": unit_of_measure.get("type", "NA"),
                    "unit_price": (
                        product.get("pricePerUnit", "NA")
                        if product.get("pricePerUnit")
                        else f"${(product.get('priceNumeric', 0) / max(unit_of_measure.get('size', 1), 1)):.2f}/100"
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
            )
        return results

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

            quantity, unit = ProductDataParser._extract_quantity_unit_from_text(
                product_name
            )
            if unit is None:
                unit = product_code.get("salesUnitType", "NA")
            if quantity is None:
                quantity = product_code.get("weightIncrement")
            quantity, unit = ProductDataParser.normalize_quantity_unit(quantity, unit)

            unit_price_string = "NA"
            if price and quantity is not None and unit in ("g", "ml"):
                try:
                    quantity_value = float(quantity)
                except (TypeError, ValueError):
                    quantity_value = None
                if quantity_value:
                    unit_price = (price / quantity_value) * 100
                    suffix = "100g" if unit == "g" else "100ml"
                    unit_price_string = f"${unit_price:.2f}/{suffix}"

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
                "quantity": quantity,
                "unit": unit,
                "unit_price": unit_price_string,
                "image": image,
            }
            result.append(product_info_map)
        return result
