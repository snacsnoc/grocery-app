Look up multiple Canadian grocers at once

Stores: 
* Presidents Choice (Superstore)
* Safeway
* SaveOnFoods
* Walmart

This app uses undocumented APIs to query search results, this project is experimental. To read more about the APIs, see `HACKING.md`

Run Flask:
```
FLASK_DEBUG=True python3 -m flask run
```

Runs on: Python 3.11, smiles

Implementation:
Taking the user's search query, the grocer's individual search API is called. To speed up sending requests, the requests are made in parallel. The data is then formatted and normalized and returned to Flask.
Data is exposed to Javascript on the search results page and then sorted accordingly.