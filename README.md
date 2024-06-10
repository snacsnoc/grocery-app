Look up multiple Canadian grocers at once
=========================================

__Stores:__
* Presidents Choice (Superstore)
* Safeway
* SaveOnFoods
* Walmart

This app uses undocumented APIs to query search results, this project is experimental. To read more about the APIs, see `HACKING.md`

Run Flask:
```
FLASK_DEBUG=True python3 -m flask run
```

Runs on: 
* Python 3.11 
* Smiles

__Implementation:__
Using the user's search query, the grocer's individual search API is called. To speed up sending requests, the requests are made in parallel. 
The users postal code to lat,long coordinates is cached to disk. This is used for store lookups, eg finding a Walmart within a proximity. This simulates behaviour from the APIs used in mobile apps.
The data is then formatted and normalized and returned to Flask.

Data is exposed to Javascript on the search results page and then sorted accordingly.

To use this in your project, or if you're just curious, the most useful files are:
* `supermarket.py` - query grocery stores, as mentioned above
* `product_data_parser.py` - parse the response from a query