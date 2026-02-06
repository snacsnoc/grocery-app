Search products in multiple Canadian grocers at once
=========================================


__Stores:__
* Presidents Choice (Superstore)
* Safeway
* SaveOnFoods
* Walmart

This app uses undocumented APIs to query search results, this project is experimental. To read more about the APIs, see `HACKING.md`

This is a backend-first skeleton project. The frontend UI is intentionally minimal and unpolished.
To use this in your project, or if you're just curious, the most useful files are:
* `supermarket.py` - query grocery stores
* `product_data_parser.py` - parse the response from a query

### Setup + run
Run Flask:
```
FLASK_DEBUG=True python3 -m flask run
```

Runs on: 
* Python 3.11 
* Smiles

__Env vars:__
* `OPENCAGE_API_KEY` - required for postal code -> lat/long
* `POSTHOG_PUB_KEY` - optional analytics for frontend
