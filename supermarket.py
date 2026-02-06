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
        if ra.status_code != 200:
            print(f"Safeway query failed: {ra.status_code}")
            return {}

        return ra.json()

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

        # Using Mac Firefox UA which is confirmed working for store search on Railway
        walmart_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:139.0) Gecko/20100101 Firefox/139.0",
            "Accept": "application/json",
            "Accept-Language": "en-CA",
            "x-o-segment": "oaoh",
            "x-o-platform": "ios",
            "X-Apollo-Operation-Name": "getPreso",
            "X-Wm-Client-Name": "glass",
            "Content-Type": "application/json",
        }

        # If we have a PX token, send it in the header as expected by iOS App
        if self.px_cookie:
            walmart_headers["X-Px-Authorization"] = f"3:{self.px_cookie}"

        walmart_cookies = {
            "deliveryCatchment": self.walmart_store_number,
            "defaultNearestStoreId": self.walmart_store_number,
        }
        walmart_data_body = {
            "operationName": "getPreso",
            "query": 'query getPreso($qy: String, $cId: String, $miPr: String, $mxPr: String, $srt: Sort, $ft: String, $intS: IntentSource, $pg: Int, $ten: String!, $pT: String!, $gn: Boolean, $pos: Int, $sT: String, $sQ: String, $rS: String, $sp: Boolean, $aO: AffinityOverride, $dGv: Boolean, $pap: String, $ptss: String, $bSId: String, $ps: Int, $fSP: JSON, $fFp: JSON, $dId: String, $iCLS: Boolean! = true, $aQP: JSON, $vr: String, $fE: Boolean! = false, $iT: Boolean! = false, $tempo: JSON, $p13n: JSON) {\n  search(\n    query: $qy\n    prg: ios\n    cat_id: $cId\n    min_price: $miPr\n    max_price: $mxPr\n    sort: $srt\n    facet: $ft\n    intentSource: $intS\n    page: $pg\n    tenant: $ten\n    channel: "Mobile"\n    pageType: $pT\n    guided_nav: $gn\n    pos: $pos\n    s_type: $sT\n    src_query: $sQ\n    recall_set: $rS\n    spelling: $sp\n    affinityOverride: $aO\n    displayGuidedNav: $dGv\n    pap: $pap\n    ptss: $ptss\n    ps: $ps\n    _be_shelf_id: $bSId\n    dealsId: $dId\n    additionalQueryParams: $aQP\n  ) {\n    __typename\n    query\n    searchResult {\n      __typename\n      ...SearchResultFragment\n    }\n  }\n  contentLayout(\n    channel: "Mobile"\n    pageType: $pT\n    tenant: $ten\n    version: $vr\n    searchArgs: {query: $qy, cat_id: $cId, facet: $ft, _be_shelf_id: $bSId, prg: ios}\n  ) @include(if: $iCLS) {\n    __typename\n    modules(p13n: $p13n, tempo: $tempo) {\n      __typename\n      schedule {\n        __typename\n        priority\n      }\n      name\n      version\n      type\n      moduleId\n      matchedTrigger {\n        __typename\n        pageId\n        zone\n        inheritable\n      }\n      triggers @include(if: $iT) {\n        __typename\n        zone\n        pageId\n        inheritable\n      }\n      configs {\n        __typename\n        ... on TempoWM_GLASSMobileDealsConfigConfigs {\n          __typename\n          deals(searchParams: $fSP) {\n            __typename\n            ...SearchResultFragment\n          }\n          pageType\n          isListing\n        }\n        ... on _TempoWM_GLASSMobileSearchGuidedNavModuleConfigs {\n          __typename\n          guidedNavigation {\n            __typename\n            ...GuidedNavigationFragment\n          }\n        }\n        ...InLineSearchBarFragment\n        ... on TempoWM_GLASSMobileBrandAmplifierAdConfigs {\n          __typename\n          ...BrandAmplifierAdFragment\n        }\n        ... on TempoWM_GLASSMobileSearchNonItemConfigs {\n          __typename\n          _rawConfigs\n          title\n          subTitle\n          urlLinkText\n          url\n        }\n        ... on TempoWM_GLASSMobileTextBannerModuleConfigs {\n          __typename\n          textBannerHeading\n          textBannerParagraph\n        }\n        ... on TempoWM_GLASSMobilePillsModuleConfigs {\n          __typename\n          moduleSource\n          pillsV2 {\n            __typename\n            ...PillsModuleFragment\n          }\n        }\n        ... on _TempoWM_GLASSMobileSearchSortFilterModuleConfigs {\n          __typename\n          facetsV1 @skip(if: $fE) {\n            __typename\n            ...FilterFragment\n          }\n          topNavFacets @include(if: $fE) {\n            __typename\n            ...FilterFragment\n          }\n        }\n        ... on TempoWM_GLASSMobileSearchBannerConfigs {\n          __typename\n          moduleType\n          viewConfig {\n            __typename\n            title\n            image\n            imageAlt\n            displayName\n            description\n            url\n            urlAlt\n            appStoreLink\n            appStoreLinkAlt\n            playStoreLink\n            playStoreLinkAlt\n          }\n        }\n        ... on TempoWM_GLASSMobileSearchSubscriptionBannerConfigs {\n          __typename\n          subscriptionBannerModuleType: moduleType\n          viewConfig {\n            __typename\n            title\n            image\n            imageAlt\n            displayName\n            description\n            url\n            urlAlt\n            appStoreLink\n            appStoreLinkAlt\n            playStoreLink\n            playStoreLinkAlt\n          }\n        }\n        ... on TempoWM_GLASSMobileSearchNonProductBannerConfigs {\n          __typename\n          nonProductBannerModuleType: moduleType\n          viewConfig {\n            __typename\n            title\n            image\n            imageAlt\n            displayName\n            description\n            url\n            urlAlt\n            appStoreLink\n            appStoreLinkAlt\n            playStoreLink\n          }\n        }\n        ... on TempoWM_GLASSMobileSearchFitmentModuleConfigs {\n          __typename\n          ...SearchFitmentModuleConfigsFragment\n        }\n        ... on _TempoWM_GLASSMobileHeadingBannerConfigs {\n          __typename\n          heading\n        }\n        ... on TempoWM_GLASSMobileSkylineDisplayAdConfigs {\n          __typename\n          ...SkylineDisplayAdFragment\n        }\n        ... on TempoWM_GLASSMobileSkinnyBannerConfigs {\n          __typename\n          ...SkinnyBannerModuleFragment\n        }\n        ... on TempoWM_GLASSMobileLocationHeadingBannerConfigs {\n          __typename\n          defaultStoreTitle\n          defaultLocationTitle\n        }\n        ... on TempoWM_GLASSMobileStoreSelectionHeaderConfigs {\n          __typename\n          fulfillmentMethodLabel\n          storeDislayName\n        }\n        ...HorizontalChipModuleConfigsFragment\n        ...EventTimerConfigsFragment\n        ...GiftFinderBannerFragment\n        ...GiftFinderFilterConfigsFragment\n        ...EarlyAccessBannerFragmentV1\n        ...EarlyAccessTimerFragmentV1\n        ...Enricher\n        ...TileTakeOverProductFragment\n        ...MarqueeDisplayFragment\n        ...MosaicGridFragment\n        ...DualMessageBannerFragment\n        ...DealsBannerFragment\n      }\n    }\n    layouts {\n      __typename\n      id\n      layout\n    }\n    pageMetadata {\n      __typename\n      location {\n        __typename\n        stateOrProvinceCode\n        postalCode\n        storeId\n        incatchment\n        spokeNodeId\n        accessPointId\n        accessType\n      }\n      pageContext\n    }\n  }\n}\nfragment SearchResultFragment on SearchInterface {\n  __typename\n  errorResponse {\n    __typename\n    source\n    errors {\n      __typename\n      errorType\n      statusCode\n      statusMsg\n      source\n    }\n  }\n  itemStacks {\n    __typename\n    meta {\n      __typename\n      ...MetadataFragment\n    }\n    itemsV2 {\n      __typename\n      ...ItemFragment\n      ...TileTakeOverTileFragment\n      ...MarqueeFragment\n      ...AdsFragment\n    }\n  }\n  pac {\n    __typename\n    relevantPT {\n      __typename\n      productType\n      score\n    }\n    showPAC\n    reasonCode\n  }\n  translation {\n    __typename\n    metadata {\n      __typename\n      originalQuery\n      translatedQuery\n      isTranslated\n      translationOfferType\n      moduleSource\n    }\n    translationModule {\n      __typename\n      title\n      urlLinkText\n      originalQueryUrl\n    }\n  }\n  shelfData {\n    __typename\n    shelfName\n  }\n  pageMetadata {\n    __typename\n    title\n    subscriptionEligible\n    location {\n      __typename\n      addressId\n    }\n    storeSelectionHeader {\n      __typename\n      fulfillmentMethodLabel\n      storeDislayName\n    }\n  }\n  requestContext {\n    __typename\n    searchMatchType\n    selectedFacetCount\n  }\n  spelling {\n    __typename\n    correctedTerm\n    originalQueryUrl\n    suggestions {\n      __typename\n      suggested\n      score\n      suggestedUrl\n    }\n  }\n  breadCrumb {\n    __typename\n    id\n    name\n    url\n    cat_level\n  }\n  paginationV2 {\n    __typename\n    maxPage\n    pageProperties\n    currentPage\n    pap {\n      __typename\n      polaris {\n        __typename\n        rerankOffset\n      }\n    }\n  }\n  modules {\n    __typename\n    guidedNavigation {\n      __typename\n      ...GuidedNavigationFragment\n    }\n    guidedNavigationV2 {\n      __typename\n      ...PillsModuleFragment\n    }\n    facetsV1 @skip(if: $fE) {\n      __typename\n      ...FilterFragment\n    }\n    topNavFacets @include(if: $fE) {\n      __typename\n      ...FacetFragment\n    }\n    allSortAndFilterFacets @include(if: $fE) {\n      __typename\n      ...FacetFragment\n    }\n    pills {\n      __typename\n      ...PillsModuleFragment\n    }\n    spellCheck {\n      __typename\n      title\n      subTitle\n      urlLinkText\n      url\n    }\n    giftFacets {\n      __typename\n      ...FacetFragment\n      values {\n        __typename\n        ...FacetFragment\n      }\n    }\n  }\n  nonProduct {\n    __typename\n    title\n    image\n    imageAlt\n    displayName\n    description\n    url\n    urlAlt\n  }\n}\nfragment MetadataFragment on Meta {\n  __typename\n  query\n  stackId\n  stackType\n  title\n  categoryTitle\n  layoutEnum\n  totalItemCount\n  totalItemCountDisplay\n  fulfillmentIntent\n  viewAllParams {\n    __typename\n    query\n    cat_id\n    sort\n    facet\n    affinityOverride\n    displayGuidedNav\n    recall_set\n    min_price\n    max_price\n  }\n  adsBeacon {\n    __typename\n    adUuid\n    moduleInfo\n    max_ads\n  }\n}\nfragment ItemFragment on Product {\n  __typename\n  id\n  usItemId\n  brand\n  name\n  type\n  canonicalUrl\n  imageInfo {\n    __typename\n    ...ProductImageInfoFragment\n  }\n  isEarlyAccessItem\n  isWplusMember\n  averageRating\n  numberOfReviews\n  esrb\n  mediaRating\n  petRx {\n    __typename\n    eligible\n    singleDispense\n  }\n  annualEvent\n  annualEventV2\n  earlyAccessEvent\n  blitzItem\n  seeShippingEligibility\n  availabilityStatus\n  checkStoreAvailabilityATC\n  fulfillmentType\n  snapEligible\n  hasCarePlans\n  availabilityStatusV2 {\n    __typename\n    value\n    display\n  }\n  productLocation {\n    __typename\n    displayValue\n    aisle {\n      __typename\n      zone\n      section\n      aisle\n    }\n  }\n  preOrder {\n    __typename\n    isPreOrder\n    preOrderMessage\n    preOrderStreetDateMessage\n  }\n  pac {\n    __typename\n    showPAC\n    reasonCode\n  }\n  weightIncrement\n  averageSoldByWeight\n  offerId\n  orderLimit\n  orderMinLimit\n  salesUnitType\n  externalInfo {\n    __typename\n    url\n  }\n  unifiedBadge: badges {\n    __typename\n    flags {\n      __typename\n      ... on BaseBadge {\n        __typename\n        id\n        text\n        key\n      }\n      ... on PreviouslyPurchasedBadge {\n        __typename\n        id\n        text\n        key\n        lastBoughtOn\n        numBought\n      }\n    }\n    tags {\n      __typename\n      ... on BaseBadge {\n        __typename\n        id\n        text\n        key\n      }\n    }\n  }\n  rewards {\n    __typename\n    cbOffer\n    description\n    eligible\n    expiry\n    minQuantity\n    promotionId\n    rewardAmt\n    selectionToken\n    state\n    term\n  }\n  offerId\n  priceInfo {\n    __typename\n    ...ProductPriceInfoFragment\n  }\n  eventAttributes {\n    __typename\n    ...EventAttributesFragment\n  }\n  currencyCode\n  variantCriteria {\n    __typename\n    ...VariantCriteriaFragment\n  }\n  sponsoredProduct {\n    __typename\n    clickBeacon\n    viewBeacon\n    spQs\n    spTags\n  }\n  showAtc\n  sellerId\n  sellerName\n  fitmentLabel\n  similarItems\n  showOptions\n  showBuyNow\n  subscription {\n    __typename\n    showSubscriptionModule\n    subscriptionEligible\n    subscriptionTransactable\n  }\n  groupMetaData {\n    __typename\n    groupType\n    groupComponents {\n      __typename\n      quantity\n      offerId\n    }\n  }\n  arExperiences {\n    __typename\n    isARHome\n    isZeekit\n  }\n}\nfragment ProductImageInfoFragment on ProductImageInfo {\n  __typename\n  thumbnailUrl\n  size\n  allImages {\n    __typename\n    ...ProductImageFragment\n  }\n}\nfragment ProductImageFragment on ProductImage {\n  __typename\n  id\n  url\n}\nfragment ProductPriceInfoFragment on ProductPriceInfo {\n  __typename\n  priceRange {\n    __typename\n    minPrice\n    maxPrice\n    priceString\n    unitOfMeasure\n  }\n  currentPrice {\n    __typename\n    ...ProductPriceFragment\n  }\n  wPlusEarlyAccessPrice {\n    __typename\n    ...WPlusEarlyAccessPriceFragment\n  }\n  unitPrice {\n    __typename\n    ...ProductPriceFragment\n  }\n  wasPrice {\n    __typename\n    ...ProductPriceFragment\n  }\n  listPrice {\n    __typename\n    ...ProductPriceFragment\n  }\n  shipPrice {\n    __typename\n    ...ProductPriceFragment\n  }\n  priceDisplayCodes {\n    __typename\n    priceDisplayCondition\n  }\n  subscriptionPrice {\n    __typename\n    priceString\n    subscriptionString\n  }\n  comparisonPrice {\n    __typename\n    ...ProductPriceFragment\n  }\n  savingsAmount {\n    __typename\n    priceString\n  }\n}\nfragment ProductPriceFragment on ProductPrice {\n  __typename\n  price\n  priceString\n  priceDisplay\n}\nfragment WPlusEarlyAccessPriceFragment on WPlusEarlyAccessPrice {\n  __typename\n  memberPrice {\n    __typename\n    ...ProductPriceFragment\n  }\n  savings {\n    __typename\n    ...ProductSavingsFragment\n  }\n  eventStartTime\n  eventStartTimeDisplay\n}\nfragment ProductSavingsFragment on ProductSavings {\n  __typename\n  amount\n  priceString\n  percent\n}\nfragment EventAttributesFragment on EventAttributes {\n  __typename\n  specialBuy\n  priceFlip\n}\nfragment VariantCriteriaFragment on VariantCriterion {\n  __typename\n  name\n  type\n  id\n  variantList {\n    __typename\n    id\n    images\n    name\n    rank\n    swatchImageUrl\n    availabilityStatus\n    products\n  }\n}\nfragment TileTakeOverTileFragment on TileTakeOverProductPlaceholder {\n  __typename\n  tileTakeOverTile {\n    __typename\n    span\n    title\n    subtitle\n    image {\n      __typename\n      title\n      src\n    }\n    logoImage {\n      __typename\n      title\n      src\n    }\n    backgroundColor\n    titleTextColor\n    subtitleTextColor\n    tileCta {\n      __typename\n      ctaLink {\n        __typename\n        clickThrough {\n          __typename\n          value\n        }\n        linkText\n        title\n      }\n      ctaType\n      ctaTextColor\n    }\n  }\n}\nfragment MarqueeFragment on MarqueePlaceholder {\n  __typename\n  marqueeType: type\n  marqueeModuleLocation: moduleLocation\n  isLazy\n}\nfragment AdsFragment on AdPlaceholder {\n  __typename\n  adsType: type\n  adsModuleLocation: moduleLocation\n  isLazy\n}\nfragment GuidedNavigationFragment on GuidedNavigationSearchInterface {\n  __typename\n  title\n  query\n  url\n  suggestionType\n}\nfragment PillsModuleFragment on PillsSearchInterface {\n  __typename\n  title\n  url\n  catID\n  suggestionType\n  catPathName\n  image: imageV1 {\n    __typename\n    src\n  }\n}\nfragment FilterFragment on Facet {\n  __typename\n  name\n  type\n  paramType\n  layout\n  min\n  max\n  selectedMin\n  selectedMax\n  unboundedMax\n  stepSize\n  isSelected\n  values {\n    __typename\n    id\n    name\n    itemCount\n    isSelected\n  }\n}\nfragment FacetFragment on Facet {\n  __typename\n  name\n  type\n  paramType\n  layout\n  min\n  max\n  selectedMin\n  selectedMax\n  unboundedMax\n  stepSize\n  isSelected\n  values {\n    __typename\n    id\n    name\n    itemCount\n    isSelected\n  }\n}\nfragment InLineSearchBarFragment on TempoWM_GLASSMobileInlineSearchConfigs {\n  __typename\n  placeholderText\n}\nfragment BrandAmplifierAdFragment on TempoWM_GLASSMobileBrandAmplifierAdConfigs {\n  __typename\n  moduleLocation\n  ad {\n    __typename\n    adContent {\n      __typename\n      data {\n        __typename\n        ...SponsoredBrandsFragment\n      }\n    }\n  }\n}\nfragment SponsoredBrandsFragment on SponsoredBrands {\n  __typename\n  adUuid\n  moduleInfo\n  brands {\n    __typename\n    logo {\n      __typename\n      featuredImage\n      featuredImageName\n      featuredUrl\n      featuredHeadline\n      logoClickTrackUrl\n    }\n    products {\n      __typename\n      ...ItemFragment\n    }\n  }\n}\nfragment SearchFitmentModuleConfigsFragment on TempoWM_GLASSMobileSearchFitmentModuleConfigs {\n  __typename\n  fitments(fitmentSearchParams: $fSP, fitmentFieldParams: $fFp) {\n    __typename\n    partTypeIDs\n    result {\n      __typename\n      status\n      extendedAttributes {\n        __typename\n        ...FitmentFieldFragment\n      }\n      formId\n      labels {\n        __typename\n        ...FitmentLabelsFragment\n      }\n      notes\n      position\n      resultSubTitle\n      suggestions {\n        __typename\n        id\n        cat_id\n        position\n        loadIndex\n        speedRating\n        searchQueryParam\n        fitmentSuggestionParams {\n          __typename\n          id\n          value\n        }\n        labels {\n          __typename\n          ...FitmentLabelsFragment\n        }\n      }\n    }\n    labels {\n      __typename\n      ...FitmentLabelsFragment\n    }\n    savedVehicle {\n      __typename\n      vehicleType {\n        __typename\n        ...FitmentVehicleFieldFragment\n      }\n      vehicleYear {\n        __typename\n        ...FitmentVehicleFieldFragment\n      }\n      vehicleMake {\n        __typename\n        ...FitmentVehicleFieldFragment\n      }\n      vehicleModel {\n        __typename\n        ...FitmentVehicleFieldFragment\n      }\n      additionalAttributes {\n        __typename\n        ...FitmentVehicleFieldFragment\n      }\n    }\n    fitmentFields {\n      __typename\n      ...FitmentVehicleFieldFragment\n    }\n    sisFitmentResponse {\n      __typename\n      ...SearchResultFragment\n    }\n    fitmentForms {\n      __typename\n      id\n      fields {\n        __typename\n        ...FitmentFieldFragment\n      }\n      title\n      labels {\n        __typename\n        ...FitmentLabelsFragment\n      }\n    }\n  }\n}\nfragment FitmentFieldFragment on FitmentField {\n  __typename\n  id\n  value\n  displayName\n  data {\n    __typename\n    label\n    value\n  }\n  extended\n  dependsOn\n}\nfragment FitmentLabelsFragment on FitmentLabels {\n  __typename\n  links {\n    __typename\n    ...FitmentLabelEntityFragment\n  }\n  messages {\n    __typename\n    ...FitmentLabelEntityFragment\n  }\n  ctas {\n    __typename\n    ...FitmentLabelEntityFragment\n  }\n  images {\n    __typename\n    ...FitmentLabelEntityFragment\n  }\n}\nfragment FitmentLabelEntityFragment on FitmentLabelEntity {\n  __typename\n  id\n  label\n  labelV1\n}\nfragment FitmentVehicleFieldFragment on FitmentVehicleField {\n  __typename\n  id\n  value\n  label\n}\nfragment SkylineDisplayAdFragment on TempoWM_GLASSMobileSkylineDisplayAdConfigs {\n  __typename\n  skylineDisplayAdModuleLocation: moduleLocation\n  enableLazyLoad\n  ad {\n    __typename\n    adContent {\n      __typename\n      data {\n        __typename\n        ... on DisplayAd {\n          __typename\n          json\n        }\n      }\n    }\n  }\n}\nfragment SkinnyBannerModuleFragment on TempoWM_GLASSMobileSkinnyBannerConfigs {\n  __typename\n  campaigns {\n    __typename\n    bannerType\n    bannerHeight\n    heading {\n      __typename\n      text\n      textColor\n    }\n    subHeading {\n      __typename\n      text\n      textColor\n    }\n    bannerCta {\n      __typename\n      ctaLink {\n        __typename\n        title\n        clickThrough {\n          __typename\n          type\n          value\n        }\n      }\n      ctaType\n      textColor\n    }\n    destination {\n      __typename\n      clickThrough {\n        __typename\n        value\n      }\n    }\n    image {\n      __typename\n      alt\n      src\n    }\n    bannerBackgroundColor\n  }\n}\nfragment HorizontalChipModuleConfigsFragment on TempoWM_GLASSWWWHorizontalChipModuleConfigs {\n  __typename\n  chipModuleSource: moduleSource\n  chipModule {\n    __typename\n    title\n    url {\n      __typename\n      linkText\n      title\n      clickThrough {\n        __typename\n        type\n        value\n        rawValue\n        tag\n      }\n    }\n  }\n  chipModuleWithImages {\n    __typename\n    title\n    url {\n      __typename\n      linkText\n      title\n      clickThrough {\n        __typename\n        type\n        value\n        rawValue\n        tag\n      }\n    }\n    image {\n      __typename\n      alt\n      assetId\n      assetName\n      clickThrough {\n        __typename\n        type\n        value\n        rawValue\n        tag\n      }\n      height\n      src\n      title\n      width\n    }\n  }\n}\nfragment EventTimerConfigsFragment on TempoWM_GLASSMobileEventTimerConfigs {\n  __typename\n  startTime\n  endTime\n  sunsetTime\n  eventName\n  preExpirationSubTextLong\n  preExpirationSubTextShort\n  postExpirationSubText\n  titleTextColor\n  defaultTextColor\n  backgroundColor\n  borderColor\n  linkBeforeExpiry {\n    __typename\n    title\n    clickThrough {\n      __typename\n      value\n    }\n  }\n  linkAfterExpiry {\n    __typename\n    title\n    clickThrough {\n      __typename\n      value\n    }\n  }\n}\nfragment GiftFinderBannerFragment on TempoWM_GLASSMobileGiftFinderBannerConfigs {\n  __typename\n  occasion {\n    __typename\n    occasionKey\n    bannerBackgroundColor\n    bannerImage {\n      __typename\n      src\n      alt\n    }\n    heading {\n      __typename\n      text\n      textColor\n    }\n  }\n}\nfragment GiftFinderFilterConfigsFragment on _TempoWM_GLASSMobileGiftFinderFiltersConfigs {\n  __typename\n  facets {\n    __typename\n    ...FacetFragment\n    values {\n      __typename\n      ...FacetFragment\n    }\n  }\n}\nfragment EarlyAccessBannerFragmentV1 on TempoWM_GLASSMobileWalmartPlusEarlyAccessBeforeEventConfigsV1 {\n  __typename\n  earlyAccessTitle\n  earlyAccessLogo {\n    __typename\n    src\n  }\n  earlyAccessCardMesssage\n  dealsSubtext1\n  dealsSubtext2\n  dealsDisclaimer\n  dealsBackground\n  beforeEventDealsLayout: dealsLayout\n  earlyAccessLink1 {\n    __typename\n    linkText\n    title\n    clickThrough {\n      __typename\n      type\n      value\n    }\n  }\n  earlyAccessLink2 {\n    __typename\n    linkText\n    title\n    clickThrough {\n      __typename\n      type\n      value\n    }\n  }\n}\nfragment EarlyAccessTimerFragmentV1 on TempoWM_GLASSMobileWalmartPlusEarlyAccessDuringEventConfigsV1 {\n  __typename\n  earlyAccessTitle\n  earlyAccessLogo {\n    __typename\n    src\n  }\n  earlyAccessCardMesssage\n  earlyAccessCounterLabel\n  earlyAccessstartTime\n  earlyAccessendTime\n  dealsBackground\n  duringEventDealsLayout: dealsLayout\n  earlyAccessLink1 {\n    __typename\n    linkText\n    title\n    clickThrough {\n      __typename\n      type\n      value\n    }\n  }\n  earlyAccessLink2 {\n    __typename\n    linkText\n    title\n    clickThrough {\n      __typename\n      type\n      value\n    }\n  }\n}\nfragment Enricher on EnricherModuleConfigsV1 {\n  __typename\n  zoneV1\n}\nfragment TileTakeOverProductFragment on TempoWM_GLASSMobileTileTakeOverProductConfigs {\n  __typename\n  slots\n  overrideDefaultTiles\n  TileTakeOverProductDetailsV1 {\n    __typename\n    pageNumber\n    span\n    position\n    title\n    subtitle\n    image {\n      __typename\n      title\n      src\n    }\n    logoImage {\n      __typename\n      title\n      src\n    }\n    backgroundColor\n    titleTextColor\n    subtitleTextColor\n    tileCta {\n      __typename\n      ctaLink {\n        __typename\n        clickThrough {\n          __typename\n          value\n        }\n        linkText\n        title\n      }\n      ctaType\n      ctaTextColor\n    }\n  }\n}\nfragment MarqueeDisplayFragment on TempoWM_GLASSMobileMarqueeDisplayAdConfigs {\n  __typename\n  ad {\n    __typename\n    adContent {\n      __typename\n      type\n    }\n  }\n  marqueeDisplayModuleLocation: moduleLocation\n  enableLazyLoad\n}\nfragment MosaicGridFragment on TempoWM_GLASSMobileMosaicGridConfigs {\n  __typename\n  paginationEnabled\n  backgroundColor\n  headerDetails {\n    __typename\n    titleDetails {\n      __typename\n      title\n      titleColor\n    }\n    subTitleDetails {\n      __typename\n      subTitle\n      subTitleColor\n    }\n  }\n  footerDetails {\n    __typename\n    backgroundColor\n    backgroundImage {\n      __typename\n      title\n      src\n    }\n    titleDetails {\n      __typename\n      title\n      titleColor\n    }\n    subTitleDetails {\n      __typename\n      subTitle\n      subTitleColor\n    }\n    ctaDetails {\n      __typename\n      ctaTitle\n      ctaTextColor\n      ctaLink\n      ctaType\n    }\n  }\n  bannerList {\n    __typename\n    backgroundColor\n    backgroundImage {\n      __typename\n      title\n      src\n    }\n    titleDetails {\n      __typename\n      title\n      titleColor\n    }\n    subTitleDetails {\n      __typename\n      subTitle\n      subTitleColor\n    }\n    ctaDetails {\n      __typename\n      ctaTitle\n      ctaTextColor\n      ctaLink\n      ctaType\n    }\n  }\n  tabList {\n    __typename\n    tabName\n    shelfId\n  }\n  dealsMosaic(searchParams: $fSP) {\n    __typename\n    itemStacks {\n      __typename\n      itemsV2 {\n        __typename\n        ...ItemFragment\n      }\n    }\n    paginationV2 {\n      __typename\n      maxPage\n      pageProperties\n      currentPage\n    }\n    errorResponse {\n      __typename\n      source\n      errors {\n        __typename\n        errorType\n        statusCode\n        statusMsg\n        source\n      }\n    }\n  }\n}\nfragment DualMessageBannerFragment on TempoWM_GLASSMobileDualMessageBannerConfigs {\n  __typename\n  backgroundImage {\n    __typename\n    alt\n    assetId\n    assetName\n    clickThrough {\n      __typename\n      type\n      value\n      rawValue\n      tag\n    }\n    height\n    src\n    title\n    width\n    size\n  }\n  secondaryBackgroundImage {\n    __typename\n    alt\n    assetId\n    assetName\n    clickThrough {\n      __typename\n      type\n      value\n      rawValue\n      tag\n    }\n    height\n    src\n    title\n    width\n    size\n  }\n  header {\n    __typename\n    title\n    fontColor\n  }\n  onlineEventStartText {\n    __typename\n    text\n    isBold\n    fontColor\n  }\n  onlineEventStartDate {\n    __typename\n    text\n    isBold\n    fontColor\n  }\n  inStoreEventStartText {\n    __typename\n    text\n    isBold\n    fontColor\n  }\n  inStoreEventStartDate {\n    __typename\n    text\n    isBold\n    fontColor\n  }\n  walmartLogoImage {\n    __typename\n    alt\n    assetId\n    assetName\n    clickThrough {\n      __typename\n      type\n      value\n      rawValue\n      tag\n    }\n    height\n    src\n    title\n    width\n    size\n  }\n  shopEarlyHeader {\n    __typename\n    text\n    isBold\n    fontColor\n  }\n  shopEarlySubHeader {\n    __typename\n    text\n    isBold\n    fontColor\n  }\n  onlineStartDate {\n    __typename\n    text\n    isBold\n    fontColor\n  }\n  earlyAccessLink1 {\n    __typename\n    linkText\n    title\n    clickThrough {\n      __typename\n      type\n      value\n    }\n  }\n  earlyAccessLink2 {\n    __typename\n    linkText\n    title\n    clickThrough {\n      __typename\n      type\n      value\n    }\n  }\n  disclaimerText\n}\nfragment DealsBannerFragment on TempoWM_GLASSMobileMobileDealsBannerConfigs {\n  __typename\n  dealsBannerBackgroundImage: backgroundImage {\n    __typename\n    alt\n    assetId\n    assetName\n    clickThrough {\n      __typename\n      type\n      value\n      rawValue\n      tag\n    }\n    height\n    src\n    title\n    width\n    size\n  }\n  primaryImage {\n    __typename\n    alt\n    assetId\n    assetName\n    clickThrough {\n      __typename\n      type\n      value\n      rawValue\n      tag\n    }\n    height\n    src\n    title\n    width\n    size\n  }\n  bannerTitle {\n    __typename\n    text\n    textColor\n  }\n  bannerMessage {\n    __typename\n    text\n    textColor\n  }\n  bannerDate {\n    __typename\n    text\n    isBold\n    textColor\n  }\n}',
            "variables": {
                "aQP": {"isMoreOptionsTileEnabled": "true"},
                "dGv": True,
                "fE": False,
                "fFp": {"powerSportEnabled": "true"},
                "fSP": {
                    "additionalQueryParams": {"isMoreOptionsTileEnabled": "true"},
                    "channel": "Mobile",
                    "displayGuidedNav": "true",
                    "page": "1",
                    "pageType": "MobileSearchPage",
                    "prg": "ios",
                    "query": self.search_query,
                    "tenant": "CA_GLASS",
                },
                "iCLS": True,
                "iT": True,
                "p13n": {
                    "page": "1",
                    "reqId": "6E9F7A17-ACE0-4D5F-AEC0-62522C13DB35",
                    "userClientInfo": {"callType": "CLIENT", "deviceType": "IOS"},
                    "userReqInfo": {
                        "refererContext": {"query": self.search_query},
                        "vid": "8B95354D-6FE8-4F18-904F-4ED9AE73EE24",
                    },
                },
                "pg": 1,
                "pT": "MobileSearchPage",
                "qy": self.search_query,
                "tempo": {},
                "ten": "CA_GLASS",
                "vr": "v1",
            },
        }
        walmart_request = None
        for attempt in range(2):
            print(f"[DEBUG] Walmart Product Query Attempt {attempt+1}")
            if self.px_cookie:
                walmart_cookies["_px3"] = self.px_cookie
                if self.px_vid:
                    walmart_cookies["_pxvid"] = self.px_vid

            walmart_request = requests.post(
                self.walmart_api_url + walmart_api_search_path,
                json=walmart_data_body,
                headers=walmart_headers,
                cookies=walmart_cookies,
                proxies=self._walmart_proxies(),
                timeout=self._walmart_timeout(),
            )

            print(f"[DEBUG] Product Query Response: {walmart_request.status_code}")

            if walmart_request.status_code == 412:
                print(
                    f"Walmart API returned 412 (Attempt {attempt+1}/2). Refreshing PX token..."
                )
                if self._refresh_walmart_px():
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
