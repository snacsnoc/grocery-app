import requests
from pymemcache.client.base import Client
import pickle
import os


# Lookup address (postal code in this case) with cache
class LocationLookupC:
    def __init__(self, api_key, cache_type="pickle"):
        self.cache_type = cache_type
        self.api_key = api_key

    def set_memcache_conf(self, memcache_ip, memcache_port):
        self.mc_client = Client(memcache_ip, memcache_port)

        """Look up the latitude and longitude for a Canadian postal code.

        Args:
            postal_code (str): A Canadian postal code.

        Returns:
            A tuple containing the latitude and longitude for the postal code, in that order.
        """

    def lookup_coords(self, postal_code):
        self.postal_code = postal_code

        if self.cache_type == "pickle":
            # Check if the results are already in the cache
            cache_filename = f"cache/postal_code_{self.postal_code}.pkl"

            if not os.path.exists(cache_filename):
                print("Postal code cache miss")
            else:
                with open(cache_filename, "rb") as f:
                    print("Postal code cache hit")
                    return pickle.load(f)
        if self.cache_type == "memcache":
            return self.mc_client.get(self.postal_code)

        # Use the OpenCage Geocoder API to look up the latitude and longitude
        api_url = f"https://api.opencagedata.com/geocode/v1/json?q={self.postal_code}&key={self.api_key}"
        response = requests.get(api_url)
        data = response.json()

        # Extract the latitude and longitude from the API response
        latitude = data["results"][0]["geometry"]["lat"]
        longitude = data["results"][0]["geometry"]["lng"]
        formatted_address = data["results"][0]["formatted"]

        if self.cache_type == "pickle":
            # Save the results to the cache
            with open(cache_filename, "wb") as f:
                pickle.dump((longitude, latitude, formatted_address), f)
        elif self.cache_type == "memcache":
            self.mc_client.set(
                self.postal_code, (longitude, latitude, formatted_address)
            )  # only stores the value if the key doesn't exist

        return longitude, latitude, formatted_address
