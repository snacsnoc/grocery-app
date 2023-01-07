#!/usr/bin/python3
#
#
#
# Copyright (c) 2022 Easton Elliott
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import requests


class SupermarketAPI:
    def __init__(self, search_query):
        self.search_query = search_query

    def search_stores_pc(self, latitude, longitude, max_results=5, search_radius=20):
        bullseye_api_url = (
            "https://ws2.bullseyelocations.com/RestSearch.svc/DoSearch2?ApiKey=9f2e82ec-18f3-407a-b91c-c6149342c389&CategoryIds=93204%2C93252&ClientId=4664&CountryId=2&FillAttr=True&FindNearestForNoResults=True&GetHoursForUpcomingWeek=True&Latitude="
            + str(latitude)
            + "&Longitude="
            + str(longitude)
            + "&MatchAllCategories=True&MaxResults="
            + str(max_results)
            + "&PageSize=5&Radius="
            + str(search_radius)
            + "&ReturnGeocode=True&SearchTypeOverride=1&StartIndex=0"
        )
        bullseye_headers = {}

        yaz = requests.get(bullseye_api_url)
        return yaz.json()

    def set_store_pc(self, store_number):
        self.store_number = store_number

    def query_pc(self, pc_store_brand="superstore"):
        pc_api_url = "https://api.pcexpress.ca/product-facade/v3/products/search"

        pc_headers = {
            "Host": "api.pcexpress.ca",
            "Accept": "application/json, text/plain, */*",
            "Site-Banner": pc_store_brand,
            "X-Apikey": "1im1hL52q9xvta16GlSdYDsTsG0dmyhF",
            "Content-Type": "application/json",
            "Origin": "https://www.realcanadiansuperstore.ca",
        }
        pc_data_query = {
            "pagination": {"from": 0, "size": 48},
            "banner": pc_store_brand,
            "cartId": "228fb500-b46f-43d2-a6c4-7b498d5be8a9",
            "lang": "en",
            "date": "05122022",
            "storeId": self.store_number,
            "pcId": False,
            "pickupType": "STORE",
            "offerType": "ALL",
            "term": self.search_query,
            "userData": {
                "domainUserId": "b3a34376-3ccf-4932-8816-7017bd33f2fc",
                "sessionId": "5580cec2-5622-4b34-8491-d94f9dd48480",
            },
        }
        self.r = requests.post(pc_api_url, json=pc_data_query, headers=pc_headers)
        # print("The status is: %s", r.status_code)

        return self.r.json()

    # Search for Save-On-Food stores given lat and long and return a JSON list
    def search_stores_saveon(self, latitude, longitude, radius=50):
        saveonfoods_api_url = (
            "https://storefrontgateway.saveonfoods.com/api/near/"
            + str(latitude)
            + "/"
            + str(longitude)
            + "/"
            + str(radius)
            + "/30/stores?shoppingModeId=11111111-1111-1111-1111-111111111111"
        )
        saveonfoods_headers = {
            "X-Correlation-Id": "4b179d51-fa67-458e-b677-9460abe2ab45",
            "X-Shopping-Mode": "11111111-1111-1111-1111-111111111111",
            "X-Site-Host": "https://www.saveonfoods.com",
            "X-Selected-Addressid": None,
            "X-Customer-Address-Latitude": latitude,
            "X-Customer-Address-Longitude": longitude,
            "X-Site-Location": "HeadersBuilderInterceptor",
            "Sec-Ch-Ua": "1",
            "Client-Route-Id": "26186555-b0d7-4251-91e1-fca38fd364aa",
            "Sec-Ch-Ua-Mobile": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36",
            "Sec-Ch-Ua-Platform": "1",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Origin": "https://www.saveonfoods.com",
            "Accept": "application/json; charset=utf-8",
        }
        store_list = requests.get(saveonfoods_api_url, headers=saveonfoods_headers)
        if store_list.status_code == 200:
            return store_list.json()

    def set_store_saveon(self, store_number):
        self.saveon_store_number = store_number

    def query_saveon(self):
        saveonfoods_api_url = "https://storefrontgateway.saveonfoods.com"
        saveonfoods_search_path = (
            "/api/stores/"
            + str(self.saveon_store_number)
            + "/preview?popularTake=30&q="
            + self.search_query
        )

        saveonfoods_headers = {
            "X-Correlation-Id": "b0bb5f7c-5c00-4cac-ae8a-f34712d0daad",
            "X-Shopping-Mode": "11111111-1111-1111-1111-111111111111",
            "X-Site-Host": "https://www.saveonfoods.com",
            "Sec-Ch-Ua": "1",
            "Client-Route-Id": "26186555-b0d7-4251-91e1-fca38fd364aa",
            "Sec-Ch-Ua-Mobile": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36",
            "Sec-Ch-Ua-Platform": "1",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Origin": "https://www.saveonfoods.com",
            "Accept": "application/json; charset=utf-8",
        }
        rad = requests.get(
            saveonfoods_api_url + saveonfoods_search_path, headers=saveonfoods_headers
        )
        # print("The status is: %s", rad.status_code)

        return rad.json()

    # get safeway
    def query_safeway(self):
        safeway_api_url = "https://voila.ca"
        safeway_search_path = (
            "/api/v5/products/search?limit=5&offset=0&sort=favorite&term="
            + self.search_query
        )

        safeway_headers = {
            "Sec-Ch-Ua": "1",
            "Client-Route-Id": "26186555-b0d7-4251-91e1-fca38fd364aa",
            "Sec-Ch-Ua-Mobile": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36",
            "Sec-Ch-Ua-Platform": "1",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Origin": "https://voila.ca",
            "Accept": "application/json; charset=utf-8",
        }

        cookies = {
            "VISITORID": "NzEyMmMzZTEtOTYzNy00MmIwLWI2NTAtNjY0NjBlZWVhOTVjOjE2NzAyMzA1NDM2NjE=",
            "global_sid": "LvSLAl2jV2YrN3AeAIbMt_Tl8DWedrNo3lJ59CxyIMI0NeYPYfzDxY2UP7FJhEdl5xSWPxf6uvxynINrmMq5p1agATEZlVMM",
        }

        ra = requests.get(
            safeway_api_url + safeway_search_path,
            headers=safeway_headers,
            cookies=cookies,
        )
        # print("The status is: %s", ra.status_code)

        return ra.json()
