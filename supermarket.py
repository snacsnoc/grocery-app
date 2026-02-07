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

import os
import sys
import time
import random
import uuid
import requests
import tls_client
import json
import re
from urllib.parse import urlencode
from walmart_px import WalmartPXGenerator


class SupermarketAPI:
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    WALMART_IOS_USER_AGENT = "WMT1H-CA/26.1 iOS/26.2"
    WALMART_IOS_PLATFORM_VERSION = "26.1.0"
    WALMART_IOS_DEVICE_MODEL = "iPhone18,1"

    def __init__(self, search_query):
        self.search_query = search_query
        self.walmart_api_url = "https://www.walmart.ca"
        self.safeway_api_url = "https://acsyshf8au-dsn.algolia.net"
        self.session = tls_client.Session(
            client_identifier="chrome_127", random_tls_extension_order=True
        )

        # Initialize WalmartPXGenerator with explicit parameters from environment or defaults
        px_app_id = os.getenv("PX_APP_ID", "PXnp9B16Cq")
        px_ft = int(os.getenv("PX_FT", "221"))
        px_collector_uri = os.getenv(
            "PX_COLLECTOR_URI",
            "https://collector-PXnp9B16Cq.px-cloud.net/api/v2/collector",
        )
        px_host = os.getenv("PX_HOST", "https://www.walmart.ca")
        px_sid = os.getenv(
            "PX_SID", str(uuid.uuid4())
        )  # Session ID, dynamic if missing
        px_vid = os.getenv(
            "PX_VID", str(uuid.uuid4())
        )  # Visitor ID, dynamic if missing
        px_cts = os.getenv(
            "PX_CTS", str(uuid.uuid4())
        )  # Challenge Timestamp/ID, dynamic if missing

        self.px_generator = WalmartPXGenerator(
            app_id=px_app_id,
            ft=px_ft,
            collector_uri=px_collector_uri,
            host=px_host,
            sid=px_sid,
            vid=px_vid,
            cts=px_cts,
        )
        self.px_cookie = None
        self.px_vid = px_vid
        self.px_uuid = None
        self.walmart_postal_code = None
        self.walmart_latlng = None
        self.walmart_device_id = os.getenv("WALMART_DEVICE_ID", str(uuid.uuid4()))
        self.safeway_store_id = None

    def _walmart_proxy(self):
        proxy_url = os.getenv("WALMART_PROXY_URL") or os.getenv("WALMART_PROXY")
        if not proxy_url:
            return None
        # Ensure proxy URL has a scheme for both tls-client and requests
        if not proxy_url.startswith("http"):
            proxy_url = f"http://{proxy_url}"
        return proxy_url

    def _walmart_proxies(self):
        proxy_url = self._walmart_proxy()
        if not proxy_url:
            return None
        return {"http": proxy_url, "https": proxy_url}

    def _walmart_timeout(self):
        try:
            return float(os.getenv("WALMART_TIMEOUT", "12"))
        except ValueError:
            return 12.0

    def _walmart_timeout_seconds(self):
        # tls-client expects an int for timeoutSeconds
        try:
            return int(float(os.getenv("WALMART_TIMEOUT", "12")))
        except ValueError:
            return 12

    def _apply_px_headers(self, headers):
        if self.px_vid:
            headers["X-Px-Vid"] = self.px_vid
        if self.px_uuid:
            headers["X-Px-Uuid"] = self.px_uuid

    def _apply_px_cookies(self, cookies):
        if not self.px_cookie:
            return
        cookies["_px3"] = self.px_cookie
        if self.px_vid:
            cookies["_pxvid"] = self.px_vid

    def _tls_request_kwargs(self, *, headers, cookies=None, params=None, data=None):
        kwargs = {
            "headers": headers,
            "timeout_seconds": self._walmart_timeout_seconds(),
        }
        if cookies is not None:
            kwargs["cookies"] = cookies
        if params is not None:
            kwargs["params"] = params
        if data is not None:
            kwargs["data"] = data
        proxy_url = self._walmart_proxy()
        if proxy_url:
            kwargs["proxy"] = proxy_url
        return kwargs

    def _extract_px3_from_do(self, response_do):
        if not response_do:
            return None
        try:
            if isinstance(response_do, list):
                do_str = "|".join([str(item) for item in response_do])
            else:
                do_str = str(response_do)
        except Exception:
            return None

        match = re.search(r"bake\|_px3\|\d+\|([^|]+)", do_str)
        if match:
            return match.group(1)
        match = re.search(r"_px3=([^|;]+)", do_str)
        if match:
            return match.group(1)
        return None

    def _extract_px_challenge(self, response):
        try:
            data = response.json()
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
        challenge = {
            "uuid": data.get("uuid"),
            "vid": data.get("vid"),
            "appId": data.get("appId"),
            "hostUrl": data.get("hostUrl"),
        }
        if any(challenge.values()):
            return challenge
        return None

    def _walmart_header_overrides(self):
        raw = os.getenv("WALMART_HEADER_OVERRIDES")
        if not raw:
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print("[DEBUG] WALMART_HEADER_OVERRIDES is not valid JSON.")
            return {}
        if not isinstance(data, dict):
            print("[DEBUG] WALMART_HEADER_OVERRIDES must be a JSON object.")
            return {}
        return {str(k): str(v) for k, v in data.items() if v is not None}

    def _walmart_cookie_overrides(self):
        raw = os.getenv("WALMART_COOKIE_OVERRIDES")
        if not raw:
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            print("[DEBUG] WALMART_COOKIE_OVERRIDES is not valid JSON.")
            return {}
        if not isinstance(data, dict):
            print("[DEBUG] WALMART_COOKIE_OVERRIDES must be a JSON object.")
            return {}
        return {str(k): str(v) for k, v in data.items() if v is not None}

    # The initial delay numbers chosen are entirely random
    def _walmart_request_delay(self):
        try:
            min_delay = float(os.getenv("WALMART_REQUEST_DELAY_MIN", "1.2"))
            max_delay = float(os.getenv("WALMART_REQUEST_DELAY_MAX", "5.1"))
        except ValueError:
            min_delay = 1.2
            max_delay = 5.1

        delay = random.uniform(min_delay, max_delay)
        print(f"[DEBUG] Delaying Walmart request by {delay:.2f} seconds...")
        time.sleep(delay)

    def _refresh_walmart_px(self, challenge=None):
        print("[DEBUG] Refreshing Walmart PX token...")
        px_uuid = None
        if challenge:
            px_uuid = challenge.get("uuid") or None
            px_vid = challenge.get("vid") or None
            px_app_id = challenge.get("appId") or None
            if px_app_id and px_app_id != self.px_generator.app_id:
                self.px_generator.app_id = px_app_id
            if px_vid:
                self.px_generator.vid = px_vid
                self.px_vid = px_vid
            if px_uuid:
                self.px_uuid = px_uuid
            print(
                "[DEBUG] PX challenge context "
                f"uuid={px_uuid or 'n/a'} vid={px_vid or 'n/a'} appId={self.px_generator.app_id}"
            )

        try:
            # Initial Payload (PX2 for V2)
            payload_data, raw_payload_1, px_uid = self.px_generator.generate_payload(
                px_uid=px_uuid
            )
            payload_body = urlencode(payload_data, safe="=")

            collector_url = self.px_generator.collector_uri

            headers = {
                "User-Agent": self.USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": self.px_generator.host,
                "Referer": self.px_generator.host + "/",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Priority": "u=1, i",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "cross-site",
                "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            }

            print(f"[DEBUG] Sending Step 1 to {collector_url}")

            def post_to_collector(step_label, body):
                response = self.session.post(
                    collector_url,
                    **self._tls_request_kwargs(headers=headers, data=body),
                )
                print(
                    f"[DEBUG] PX Collector {step_label} status: {response.status_code}"
                )
                print(
                    f"[DEBUG] PX Collector {step_label} cookies: {list(response.cookies.keys())}"
                )
                return response

            r = post_to_collector("Step 1", payload_body)

            if r.status_code == 200:
                if "_px3" in r.cookies:
                    self.px_cookie = r.cookies["_px3"]
                    print(
                        f"[DEBUG] Successfully obtained _px3 cookie in Step 1: {self.px_cookie[:20]}..."
                    )
                    return True

                try:
                    data = r.json()
                    if "do" in data:
                        # Even if we find a token in 'do', we should usually proceed to Step 2
                        # because 'do' implies a challenge. The token might be a temp one
                        px3_from_do = self._extract_px3_from_do(data.get("do"))
                        if px3_from_do:
                            print(
                                f"[DEBUG] Found _px3 in Step 1 'do', but proceeding to Step 2 to solve challenge..."
                            )
                            # We can store it tentatively, but don't return yet
                            self.px_cookie = px3_from_do

                        print(
                            f"[DEBUG] Received Challenge in Step 1. Attempting Step 2..."
                        )
                        challenge_data = self.px_generator.generate_challenge_payload(
                            raw_payload_1,
                            data["do"],
                            px_uid,
                            sid=self.px_generator.sid,
                            vid=self.px_generator.vid,
                            cts=self.px_generator.cts,
                        )
                        challenge_body = urlencode(challenge_data, safe="=")

                        r2 = post_to_collector("Step 2", challenge_body)

                        if r2.status_code == 200:
                            if "_px3" in r2.cookies:
                                self.px_cookie = r2.cookies["_px3"]
                                print(
                                    f"[DEBUG] Successfully obtained _px3 cookie in Step 2: {self.px_cookie[:20]}..."
                                )
                                return True

                            data2 = r2.json()
                            if "do" in data2:
                                px3_from_do = self._extract_px3_from_do(data2.get("do"))
                                if px3_from_do:
                                    self.px_cookie = px3_from_do
                                    print(
                                        f"[DEBUG] Extracted _px3 from JSON in Step 2: {self.px_cookie[:20]}..."
                                    )
                                    return True
                                print(
                                    "[DEBUG] Step 2 JSON contained 'do' but no _px3 token was found."
                                )
                            else:
                                print(f"[DEBUG] Step 2 JSON keys: {list(data2.keys())}")
                                print(f"[DEBUG] Step 2 body snippet: {r2.text[:200]}")

                        # If Step 2 failed but we found a token in Step 1, maybe fallback to it?
                        if self.px_cookie:
                            print(
                                "[DEBUG] Step 2 yielded no new token, using token from Step 1/Tentative."
                            )
                            return True

                    else:
                        print(f"[DEBUG] Step 1 JSON keys: {list(data.keys())}")
                        print(f"[DEBUG] Step 1 body snippet: {r.text[:200]}")
                except:
                    print(f"[DEBUG] Step 1 Response not JSON: {r.text[:200]}")

            else:
                print(f"[DEBUG] PX Collector Step 1 failed: {r.status_code}")
                print(f"[DEBUG] PX Collector Step 1 body snippet: {r.text[:200]}")

        except Exception as e:
            print(f"[DEBUG] Error refreshing PX token: {e}")

        return False

    def search_stores_pc(
        self,
        latitude,
        longitude,
        max_results=5,
        search_radius=20,
        store_brand="superstore",
    ):
        category_id = ""
        # Set search category, see HACKING.md
        if store_brand == "superstore":
            category_id = "93204"
        elif store_brand == "other":
            category_id = "93252"
        elif store_brand == "all":
            category_id = ""

        bullseye_api_url = (
            "https://ws2.bullseyelocations.com/RestSearch.svc/DoSearch2?ApiKey=9f2e82ec-18f3-407a-b91c-c6149342c389"
            + "&CategoryIds="
            + category_id
            + "&ClientId=4664&CountryId=2&FillAttr=True&FindNearestForNoResults=True&GetHoursForUpcomingWeek=True&Latitude="
            + str(latitude)
            + "&Longitude="
            + str(longitude)
            + "&MatchAllCategories=True&MaxResults="
            + str(max_results)
            + "&PageSize=5&Radius="
            + str(search_radius)
            + "&ReturnGeocode=True&SearchTypeOverride=1&StartIndex=0"
        )

        self.r = requests.get(bullseye_api_url)

        return self.r.json()

    def set_store_pc(self, store_number):
        self.pc_store_number = store_number

    def query_pc(self, pc_store_brand="superstore"):
        pc_api_url = "https://api.pcexpress.ca/pcx-bff/api/v2/products/search"

        pc_headers = {
            "Host": "api.pcexpress.ca",
            "Sec-Ch-Ua": '"Chromium";v="125", "Not.A/Brand";v="24"',
            "Is-Helios-Account": "false",
            "X-Application-Type": "Web",
            "X-Preview": "false",
            "X-Apikey": "C1xujSegT5j3ap3yexJjqhOfELwGKYvz",
            "Accept-Language": "en",
            "Sec-Ch-Ua-Mobile": "?0",
            "Is-Iceberg-Enabled": "true",
            "User-Agent": "Mozilla/5.0 (Linux; U; Android 2.2; en-us; Droid Build/FRG22D) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
            "X-Channel": "web",
            "Content-Type": "application/json",
            "Origin_session_header": "B",
            "X-Loblaw-Tenant-Id": "ONLINE_GROCERIES",
            "Business-User-Agent": "PCXWEB",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Accept": "*/*",
            "Origin": "https://www.realcanadiansuperstore.ca",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://www.realcanadiansuperstore.ca/",
            "Priority": "u=1, i",
            "Connection": "keep-alive",
        }
        pc_data_query = json.dumps(
            {
                "cart": {"cartId": "5f034336-4031-41f0-aade-050314cb6c21"},
                "fulfillmentInfo": {
                    "storeId": self.pc_store_number,
                    "pickupType": "STORE",
                    "offerType": "OG",
                    "date": "23062025",
                    "timeSlot": None,
                },
                "listingInfo": {
                    "filters": {"search-bar": [self.search_query]},
                    "sort": {},
                    "pagination": {"from": 1},
                    "includeFiltersInResponse": False,
                },
                "banner": pc_store_brand,
                "userData": {
                    "domainUserId": "c0de9603-5588-4e6a-8cb4-0d481182c109",
                    "sessionId": "de1e6a77-f510-47bf-944c-71bf0cc50745",
                },
                "device": {"screenSize": 1358},
                "searchRelatedInfo": {
                    "term": self.search_query,
                    "options": [{"name": "rmp.unifiedSearchVariant", "value": "Y"}],
                },
            }
        )
        self.r = requests.post(pc_api_url, headers=pc_headers, data=pc_data_query)
        if self.r.status_code == 200:
            return self.r.json()
        else:
            return None

    # Search for Save-On-Food stores given lat, long and radius in KM and return a JSON list
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
            "X-Customer-Address-Latitude": str(latitude),
            "X-Customer-Address-Longitude": str(longitude),
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

    def search_stores_safeway(self, latitude, longitude, max_results=4):
        request_url = f"{self.safeway_api_url}/1/indexes/dxp_stores/query"
        params = {
            "x-algolia-agent": "Algolia for JavaScript (5.46.3); Search (5.46.3); Browser",
            "x-algolia-api-key": "626ed0e489d96920499cef24b4dd25d6",
            "x-algolia-application-id": "ACSYSHF8AU",
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://www.safeway.ca",
            "Referer": "https://www.safeway.ca/",
            "User-Agent": self.USER_AGENT,
        }
        payload = {
            "query": "",
            "aroundLatLng": f"{latitude}, {longitude}",
            "hitsPerPage": max_results,
            "page": 0,
            "aroundRadius": "all",
            "filters": "bannerCode:'Safeway'",
            "facets": ["departments.type", "address.province"],
            "analyticsTags": ["C", "website"],
        }

        response = requests.post(
            request_url,
            params=params,
            headers=headers,
            json=payload,
        )

        if response.status_code != 200:
            print(f"[DEBUG] Safeway store search failed: {response.status_code}")
            print(f"[DEBUG] Safeway store search snippet: {response.text[:200]}")
            return {}

        try:
            return response.json()
        except ValueError:
            print(f"[DEBUG] Safeway store search not JSON: {response.text[:200]}")
            return {}

    def set_store_safeway(self, store_id):
        self.safeway_store_id = store_id

    # get safeway
    def query_safeway(self, hits_per_page=30):
        if not self.safeway_store_id:
            print("[DEBUG] Safeway store ID not set; skipping query.")
            return {}

        request_url = f"{self.safeway_api_url}/1/indexes/*/queries"
        params = {
            "x-algolia-agent": "Algolia for JavaScript (5.46.3); Search (5.46.3); Browser",
            "x-algolia-api-key": "626ed0e489d96920499cef24b4dd25d6",
            "x-algolia-application-id": "ACSYSHF8AU",
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://www.safeway.ca",
            "Referer": "https://www.safeway.ca/",
            "User-Agent": self.USER_AGENT,
        }
        payload = {
            "requests": [
                {
                    "indexName": "dxp_product_en",
                    "query": self.search_query,
                    "hitsPerPage": hits_per_page,
                    "clickAnalytics": True,
                    "userToken": "",
                    "filters": (
                        f"storeId:{self.safeway_store_id} "
                        "AND isVisible:true AND isMassOffers:false"
                    ),
                    "analyticsTags": ["C", "website"],
                },
                {
                    "indexName": "dxp_product_en_query_suggestions",
                    "query": self.search_query,
                    "hitsPerPage": 5,
                    "clickAnalytics": True,
                    "userToken": "",
                },
            ]
        }

        response = requests.post(
            request_url,
            params=params,
            headers=headers,
            json=payload,
        )

        print(f"[DEBUG] Safeway product search URL: {request_url}")
        print(f"[DEBUG] Safeway product search status: {response.status_code}")
        if response.status_code != 200:
            print(f"[DEBUG] Safeway product search failed: {response.status_code}")
            print(f"[DEBUG] Safeway product search snippet: {response.text[:200]}")
            return {}

        try:
            data = response.json()
            hits = data.get("results", [{}])[0].get("hits", [])
            print(f"[DEBUG] Safeway product search hits: {len(hits)}")
            if hits:
                print(
                    f"[DEBUG] Safeway product search first hit keys: {list(hits[0].keys())}"
                )
            return data
        except ValueError:
            print(f"[DEBUG] Safeway product search not JSON: {response.text[:200]}")
            return {}

    def search_stores_walmart(self, postal_code, latitude=None, longitude=None):
        # Default to the FetchNearByNodes endpoint; fall back to PX if blocked
        postal_code = postal_code.replace(" ", "").upper()
        formatted_postal_code = f"{postal_code[:3]} {postal_code[3:]}"
        self.walmart_postal_code = postal_code
        if latitude is not None and longitude is not None:
            self.walmart_latlng = f"{latitude},{longitude}"
        else:
            self.walmart_latlng = None

        fetch_near_by_nodes_hash = (
            "13cc7c54f667f47fc364643da028af42bb68c795ddf6da8733aca6559b41c53f"
        )
        variables = {
            "checkInventoryFlow": False,
            "input": {
                "accessTypes": [
                    "PICKUP_CURBSIDE",
                    "PICKUP_INSTORE",
                    "PICKUP_SPOKE",
                    "PICKUP_POPUP",
                ],
                "city": None,
                "latitude": float(latitude) if latitude else None,
                "longitude": float(longitude) if longitude else None,
                "nodeTypes": ["STORE", "PICKUP_SPOKE", "PICKUP_POPUP"],
                "partnerIds": None,
                "postalCode": formatted_postal_code,
                "stateOrProvince": None,
            },
        }
        walmart_api_search_path = (
            f"/orchestra/cartxo/graphql/FetchNearByNodes/{fetch_near_by_nodes_hash}"
        )
        walmart_api_search_params = {
            "id": fetch_near_by_nodes_hash,
            "variables": json.dumps(variables, separators=(",", ":")),
        }

        walmart_headers = {
            "User-Agent": self.WALMART_IOS_USER_AGENT,
            "Accept": "*/*",
            "Accept-Language": "en-CA",
            "tenant-id": "qxjed8",
            "x-o-platform": "ios",
            "x-o-platform-version": self.WALMART_IOS_PLATFORM_VERSION,
            "x-o-device": self.WALMART_IOS_DEVICE_MODEL,
            "x-o-device-id": self.walmart_device_id,
            "x-o-segment": "oaoh",
            "x-o-tp-phase": "tp5",
            "x-o-bu": "WALMART-CA",
            "x-o-mart": "B2C",
            "x-o-gql-query": "query FetchNearByNodes",
            "X-Apollo-Operation-Name": "FetchNearByNodes",
            "X-Apollo-Operation-Id": fetch_near_by_nodes_hash,
            "X-Wm-Client-Name": "glass",
            "X-Wm-Vid": self.px_vid,
            "X-Wm-Sid": self.px_generator.sid,
            "X-Enable-Server-Timing": "1",
            "X-Latency-Trace": "1",
            "Wm_mp": "true",
        }
        self._apply_px_headers(walmart_headers)
        if self.px_cookie:
            walmart_headers["X-Px-Authorization"] = f"3:{self.px_cookie}"

        walmart_cookies = {
            "walmart.nearestPostalCode": postal_code,
            "wmt.c": "0",
        }
        if latitude is not None and longitude is not None:
            walmart_cookies["walmart.nearestLatLng"] = f"{latitude},{longitude}"

        # Add a human-like delay before the first store lookup
        self._walmart_request_delay()

        response = None
        for attempt in range(3):
            print(f"[DEBUG] Walmart Store Search Attempt {attempt+1}")
            if attempt > 0 and self.px_cookie:
                print(f"[DEBUG] Attaching PX Cookie: {self.px_cookie[:15]}...")
                self._apply_px_cookies(walmart_cookies)
                self._apply_px_headers(walmart_headers)

            walmart_headers.update(self._walmart_header_overrides())
            walmart_cookies.update(self._walmart_cookie_overrides())

            response = self.session.get(
                self.walmart_api_url + walmart_api_search_path,
                **self._tls_request_kwargs(
                    headers=walmart_headers,
                    cookies=walmart_cookies,
                    params=walmart_api_search_params,
                ),
            )

            print(f"[DEBUG] Store Search Response: {response.status_code}")
            # print(f"[DEBUG] Store Search Body: {response.text[:1000]}") # Uncomment if needed

            # Handle PX challenge
            if response.status_code == 412:
                challenge = self._extract_px_challenge(response)
                if challenge:
                    print(
                        "[DEBUG] PX challenge "
                        f"uuid={challenge.get('uuid') or 'n/a'} vid={challenge.get('vid') or 'n/a'}"
                    )
                print(
                    f"Walmart API returned 412 (Attempt {attempt+1}/3). Refreshing PX token..."
                )
                if self._refresh_walmart_px(challenge=challenge):
                    # walmart_headers["X-Px-Authorization"] = f"3:{self.px_cookie}"
                    self._apply_px_cookies(walmart_cookies)
                    continue
                print("[DEBUG] PX refresh failed; returning 412 response.")

            # Handle rate limiting
            if response.status_code == 429:
                print(
                    f"Walmart API returned 429 (Attempt {attempt+1}/3). Refreshing PX token..."
                )
                if self._refresh_walmart_px():
                    # walmart_headers["X-Px-Authorization"] = f"3:{self.px_cookie}"
                    self._apply_px_cookies(walmart_cookies)
                delay = random.uniform(3, 7) * (attempt + 1)
                print(f"[DEBUG] Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                continue

            # If we get a successful response, add the cookie to our session
            if "_px3" in response.cookies:
                self.px_cookie = response.cookies["_px3"]

            # If not 412/429 or refresh failed, break
            break

        if response.status_code != 200:
            return {
                "_error": "http_status",
                "_status": response.status_code,
                "_body": (response.text or "")[:1000],
            }

        try:
            data = response.json()
            if isinstance(data, dict):
                data["_status"] = response.status_code
            return data
        except ValueError:
            return {
                "_error": "invalid_json",
                "_status": response.status_code,
                "_body": (response.text or "")[:1000],
            }

    # Set Walmart store by ID
    def set_store_walmart(self, store_id):
        self.walmart_store_number = store_id

    # Query Walmart search by store ID
    def query_walmart(self):
        self._walmart_request_delay()
        # Using GET endpoint and persisted hash from iOS intercept
        persisted_hash = (
            "abe71b798bb572e81f953ec17132900f84218712d206b57b0e9d4d32e619e8f6"
        )

        variables = {
            "aQP": {
                "isDynamicFacetsEnabled": True,
                "isGenAiEnabled": False,
                "isMoreOptionsTileEnabled": True,
            },
            "contentLayoutVersion": "v1",
            "dGv": False,
            "fFp": {"dynamicFitmentEnabled": True, "powerSportEnabled": True},
            "fSP": {
                "channel": "Mobile",
                "displayGuidedNav": False,
                "facet": "fulfillment_method:Pickup",
                "page": 1,
                "pageType": "MobileSearchPage",
                "prg": "ios",
                "query": self.search_query,
                "spelling": True,
                "tenant": "CA_GLASS",
            },
            "ft": "fulfillment_method:Pickup",
            "iCLS": True,
            "p13n": {
                "page": 1,
                "userClientInfo": {"callType": "CLIENT", "deviceType": "IOS"},
                "userReqInfo": {
                    "isMoreOptionsTileEnabled": True,
                    "refererContext": {"query": self.search_query},
                    "vid": "62E7E52A-8C33-4E14-810B-46225509222E",
                },
            },
            "pg": 1,
            "pT": "MobileSearchPage",
            "qy": self.search_query,
            "ten": "CA_GLASS",
        }

        params = {
            "query": self.search_query,
            "facet": "fulfillment_method:Pickup",
            "page": "1",
            "spelling": "true",
            "displayGuidedNav": "false",
            "additionalQueryParams": '{"isGenAiEnabled":false,"isMoreOptionsTileEnabled":true,"isDynamicFacetsEnabled":true,"isModuleArrayReq":false}',
            "id": persisted_hash,
            "variables": json.dumps(variables),
        }

        walmart_headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "application/json",
            "Accept-Language": "en-CA",
            "x-o-platform": "rweb",
            "x-o-gql-query": "query getPreso",
            "X-Apollo-Operation-Name": "getPreso",
            "X-Wm-Client-Name": "glass",
            "x-o-bu": "WALMART-CA",
            "x-o-mart": "B2C",
            "tenant-id": "qxjed8",
        }
        self._apply_px_headers(walmart_headers)

        walmart_cookies = {
            "deliveryCatchment": self.walmart_store_number,
            "defaultNearestStoreId": self.walmart_store_number,
            "wmt.c": "0",
        }
        if self.walmart_postal_code:
            walmart_cookies["walmart.nearestPostalCode"] = self.walmart_postal_code
        if self.walmart_latlng:
            walmart_cookies["walmart.nearestLatLng"] = self.walmart_latlng
        if self.px_cookie:
            walmart_headers["X-Px-Authorization"] = f"3:{self.px_cookie}"
            self._apply_px_cookies(walmart_cookies)
            self._apply_px_headers(walmart_headers)

        walmart_headers.update(self._walmart_header_overrides())
        walmart_cookies.update(self._walmart_cookie_overrides())

        walmart_request = None
        for attempt in range(2):
            print(f"[DEBUG] Walmart Product Query Attempt {attempt+1}")

            # Prepare request for logging
            request_url = f"{self.walmart_api_url}/orchestra/snb/graphql/getPreso/{persisted_hash}/search"

            # Enhanced Debug Logging
            print(f"[DEBUG] Request URL: {request_url}")
            print(f"[DEBUG] Request Params: {json.dumps(params, indent=2)}")
            print(f"[DEBUG] Request Headers: {json.dumps(walmart_headers, indent=2)}")

            # Anonymize PX cookie for logging
            logged_cookies = walmart_cookies.copy()
            if "_px3" in logged_cookies:
                logged_cookies["_px3"] = logged_cookies["_px3"][:20] + "..."
            print(f"[DEBUG] Request Cookies: {json.dumps(logged_cookies, indent=2)}")

            walmart_request = self.session.get(
                request_url,
                **self._tls_request_kwargs(
                    headers=walmart_headers,
                    cookies=walmart_cookies,
                    params=params,
                ),
            )

            print(f"[DEBUG] Product Query Response: {walmart_request.status_code}")

            if walmart_request.status_code == 412:
                print(
                    f"Walmart API returned 412 (Attempt {attempt+1}/2). Refreshing PX token..."
                )
                if self._refresh_walmart_px():
                    walmart_headers["X-Px-Authorization"] = f"3:{self.px_cookie}"
                    continue
            break

        if walmart_request.status_code != 200:
            return {
                "_error": "http_status",
                "_status": walmart_request.status_code,
                "_body": (walmart_request.text or "")[:1000],
            }

        try:
            data = walmart_request.json()
            if isinstance(data, dict):
                data["_status"] = walmart_request.status_code
            return data
        except ValueError:
            return {
                "_error": "invalid_json",
                "_status": walmart_request.status_code,
                "_body": (walmart_request.text or "")[:1000],
            }
