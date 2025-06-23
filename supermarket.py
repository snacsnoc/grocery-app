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
import json


class SupermarketAPI:
    def __init__(self, search_query):
        self.search_query = search_query
        self.walmart_api_url = "https://www.walmart.ca"

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
        self.store_number = store_number

    def query_pc(self, pc_store_brand="superstore"):
        pc_api_url = "https://api.pcexpress.ca/pcx-bff/api/v2/products/search"

        pc_headers = {
            "Host": "api.pcexpress.ca",
            "Content-Length": "552",
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
                    "storeId": self.store_number,
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

        return ra.json()

    def search_stores_walmart(self, postal_code):

        # Format the postal code as per the URL params
        formatted_postal_code = postal_code[:3] + "%20" + postal_code[3:]

        walmart_api_search_path = f"/orchestra/graphql/nearByNodes/383d44ac5962240870e513c4f53bb3d05a143fd7b19acb32e8a83e39f1ed266c?variables=%7B%22input%22%3A%7B%22postalCode%22%3A%22{formatted_postal_code}%22%2C%22accessTypes%22%3A%5B%22PICKUP_INSTORE%22%2C%22PICKUP_CURBSIDE%22%5D%2C%22nodeTypes%22%3A%5B%22STORE%22%2C%22PICKUP_SPOKE%22%2C%22PICKUP_POPUP%22%5D%2C%22latitude%22%3Anull%2C%22longitude%22%3Anull%2C%22radius%22%3Anull%7D%2C%22checkItemAvailability%22%3Afalse%2C%22checkWeeklyReservation%22%3Afalse%2C%22enableStoreSelectorMarketplacePickup%22%3Afalse%2C%22enableVisionStoreSelector%22%3Afalse%2C%22enableStorePagesAndFinderPhase2%22%3Afalse%2C%22enableStoreBrandFormat%22%3Afalse%2C%22disableNodeAddressPostalCode%22%3Afalse%7D"

        walmart_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:139.0) Gecko/20100101 Firefox/139.0",
            "Accept": "application/json",
            "Accept-Language": "en-CA",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://www.walmart.ca/en/browse/grocery/dairy-eggs/dairy-milk/2-milk/10019_6000194327369_6000194327399_6000194349400",
            "x-o-segment": "oaoh",
            "x-o-platform-version": "caweb-1.134.0-36c66ff8bec9d3214adcf2e2d56466ca4fb2fd72-6162053r",
            "x-o-correlation-id": "ior0M7_srhMZECBAFc0aRuBRx1Ue3fHRMx7R",
            "wm_qos.correlation_id": "ior0M7_srhMZECBAFc0aRuBRx1Ue3fHRMx7R",
            "WM_MP": "true",
            "Content-Type": "application/json",
            "x-o-ccm": "server",
            "x-o-gql-query": "query nearByNodes",
            "X-APOLLO-OPERATION-NAME": "nearByNodes",
            "x-latency-trace": "1",
            "x-enable-server-timing": "1",
            "traceparent": "00-184b9cf0a347a25bd2d2056195ea715f-c2a8decc29ce1cf9-00",
            "WM_PAGE_URL": "https://www.walmart.ca/en/browse/grocery/dairy-eggs/dairy-milk/2-milk/10019_6000194327369_6000194327399_6000194349400",
            "baggage": "trafficType=customer,deviceType=desktop,renderScope=SSR,webRequestSource=Browser,pageName=unknown,isomorphicSessionId=eFYhDl9lXRYjUuvAY08Mp,renderViewId=50bdbc61-331f-4308-9eaa-ecd6f3442b4a",
            "x-o-platform": "rweb",
            "tenant-id": "qxjed8",
            "x-o-bu": "WALMART-CA",
            "x-o-mart": "B2C",
            "Connection": "keep-alive",
            "Cookie": 'TS010110a1=0151d97a5649488ee95f03fddee8772471d754fb077826fed6c2f923a5dfe20b4de421f7ae1b6cefad30abe22ab08bc367c4a23057; TS01ea8d4c=0151d97a5649488ee95f03fddee8772471d754fb077826fed6c2f923a5dfe20b4de421f7ae1b6cefad30abe22ab08bc367c4a23057; TS0180da25=0151d97a5649488ee95f03fddee8772471d754fb077826fed6c2f923a5dfe20b4de421f7ae1b6cefad30abe22ab08bc367c4a23057; TSe62c5f0d027=089fde974cab200056a15ddfae1437dfcd750532c8a88b242074b3c86ce84ddb4ef1e783299becc80891543a581130007e37d92811e9a9fb38bf6e6cb6742f143c7cb7e99ce613d634bc2746dca968ea7a00101cfd2204291442e2f4bb11aa5a; headerType=whiteGM; DYN_USER_ID.ro=325b274d-49d5-41b5-bbc9-a6af2b60bec7; authDuration={"lat":"1735169327091000","lt":"1735169327091000"}; ak-ca-origin-route=legacy; TS01f0f358=01cfee4702c15f491121d6d079ebc09ed921b8ccca76e7a6969b188fac194b14dd5773b5a60bb3fe9909a4f93a33843edfd0fb0501; pxcts=fe36dcee-c317-11ef-a695-5cb4b5f45bad; wm_route_based_language=en-CA; LT=1741089993504; ak-ca-origin-route=legacy; auth=MTAyOTYyMDE4DE6jyfPo1d0E2zZ4Qn248x49F9uxVXrhRGdlDiX7fOjOZgEmxAwCRz8VRqGCgVAl81SurlRcpR1%2FeQ8yCgUU%2BJhgXP897VOC97CDlGf0k1S7rww66Q8cUDNyc%2F3DSOaxj8OFN4dileb20bpDLeCIlSFd%2FHsc7bnSe4%2BTLU2zbj17CYdpegknYU0Zi4y2T9fCpUTATi2CsUm%2B03hZmSXOfn2Kw%2Fl4U8z%2BMCFULom2MUGWRXS%2FVM7dhoO5fDBksK28pGd2w9VMvEOMsmi01MtA%2Fwy6yd1WbYCmt0ZvUnNBajWGjRlKwaB3hGjglkYV8afcQ0x%2BtqZcZN2F9J5P8RFumktq03mxyRIb%2BsIQfpgZXiaYkViBJfVltOdZpQemsAY8UqOWoNqTXTPsacbfXQLAoyCFU7YNy%2B%2B7Og%2FK1CpgYd8%3D; ACID=addfcdbc-828e-4cf2-92bc-32943fbfd58d; hasACID=true; locDataV3=eyJpc0RlZmF1bHRlZCI6ZmFsc2UsImlzRXhwbGljaXQiOmZhbHNlLCJpbnRlbnQiOiJERUxJVkVSWSIsInBpY2t1cCI6W3sibm9kZUlkIjoiMTEwNCIsImRpc3BsYXlOYW1lIjoiVkFOQ09VVkVSLCBCQyIsImFkZHJlc3MiOnsicG9zdGFsQ29kZSI6IlY1TSAyRzciLCJhZGRyZXNzTGluZTEiOiIzNTg1IEdSQU5EVklFVyBIV1kiLCJjaXR5IjoiVmFuY291dmVyIiwic3RhdGUiOiJCQyIsImNvdW50cnkiOiJDQSJ9LCJnZW9Qb2ludCI6eyJsYXRpdHVkZSI6NDkuMjU5MjQ2LCJsb25naXR1ZGUiOi0xMjMuMDI3NDQ2fSwic2NoZWR1bGVkRW5hYmxlZCI6dHJ1ZSwidW5TY2hlZHVsZWRFbmFibGVkIjpmYWxzZSwic3RvcmVIcnMiOiIwNzowMC0yMzowMCIsInN1cHBvcnRlZEFjY2Vzc1R5cGVzIjpbIlBJQ0tVUF9DVVJCU0lERSIsIlBJQ0tVUF9JTlNUT1JFIl0sInRpbWVab25lIjoiUFNUIiwic3RvcmVCcmFuZEZvcm1hdCI6IldhbG1hcnQgU3VwZXJjZW50ZXIiLCJzZWxlY3Rpb25UeXBlIjoiTFNfU0VMRUNURUQifV0sInNoaXBwaW5nQWRkcmVzcyI6eyJsYXRpdHVkZSI6NDkuMjQ3NDU4MiwibG9uZ2l0dWRlIjotMTIzLjEyMTU0MTIsInBvc3RhbENvZGUiOiJWNVogOVowIiwiY2l0eSI6IlZhbmNvdXZlciIsInN0YXRlIjoiQkMiLCJjb3VudHJ5Q29kZSI6IkNBIiwibG9jYXRpb25BY2N1cmFjeSI6ImxvdyIsImdpZnRBZGRyZXNzIjpmYWxzZX0sImFzc29ydG1lbnQiOnsibm9kZUlkIjoiMTEwNCIsImRpc3BsYXlOYW1lIjoiVkFOQ09VVkVSLCBCQyIsImFjY2Vzc1BvaW50cyI6W3siYWNjZXNzVHlwZSI6IkRFTElWRVJZX0FERFJFU1MifV0sInN1cHBvcnRlZEFjY2Vzc1R5cGVzIjpbIkRFTElWRVJZX0FERFJFU1MiXSwiaW50ZW50IjoiREVMSVZFUlkifSwiaW5zdG9yZSI6ZmFsc2UsImRlbGl2ZXJ5Ijp7Im5vZGVJZCI6IjExMDQiLCJkaXNwbGF5TmFtZSI6IlZBTkNPVVZFUiwgQkMiLCJhZGRyZXNzIjp7InBvc3RhbENvZGUiOiJWNU0gMkc3IiwiYWRkcmVzc0xpbmUxIjoiMzU4NSBHUkFORFZJRVcgSFdZIiwiY2l0eSI6IlZhbmNvdXZlciIsInN0YXRlIjoiQkMiLCJjb3VudHJ5IjoiQ0EifSwiZ2VvUG9pbnQiOnsibGF0aXR1ZGUiOjQ5LjI1OTI0NiwibG9uZ2l0dWRlIjotMTIzLjAyNzQ0Nn0sInNjaGVkdWxlZEVuYWJsZWQiOmZhbHNlLCJ1blNjaGVkdWxlZEVuYWJsZWQiOmZhbHNlLCJhY2Nlc3NQb2ludHMiOlt7ImFjY2Vzc1R5cGUiOiJERUxJVkVSWV9BRERSRVNTIn1dLCJpc0V4cHJlc3NEZWxpdmVyeU9ubHkiOmZhbHNlLCJzdXBwb3J0ZWRBY2Nlc3NUeXBlcyI6WyJERUxJVkVSWV9BRERSRVNTIl0sInRpbWVab25lIjoiQW1lcmljYS9WYW5jb3V2ZXIiLCJzdG9yZUJyYW5kRm9ybWF0IjoiV2FsbWFydCBTdXBlcmNlbnRlciIsInNlbGVjdGlvblR5cGUiOiJMU19TRUxFQ1RFRCJ9LCJpc2dlb0ludGxVc2VyIjpmYWxzZSwibXBEZWxTdG9yZUNvdW50IjowLCJyZWZyZXNoQXQiOjE3NTA2ODcwMDY3MDYsInZhbGlkYXRlS2V5IjoicHJvZDp2MzphZGRmY2RiYy04MjhlLTRjZjItOTJiYy0zMjk0M2ZiZmQ1OGQifQ==; assortmentStoreId=1104; _shcc=CA; _intlbu=false; hasLocData=1; locGuestData=eyJpbnRlbnQiOiJERUxJVkVSWSIsImlzRXhwbGljaXQiOmZhbHNlLCJzdG9yZUludGVudCI6IkRFTElWRVJZIiwibWVyZ2VGbGFnIjpmYWxzZSwiaXNEZWZhdWx0ZWQiOmZhbHNlLCJwaWNrdXAiOnsibm9kZUlkIjoiMTEwNCIsInRpbWVzdGFtcCI6MTc1MDY2NTQwNjcwNSwic2VsZWN0aW9uVHlwZSI6IkxTX1NFTEVDVEVEIiwic2VsZWN0aW9uU291cmNlIjoiSVBfU05JRkZFRF9CWV9MUyJ9LCJzaGlwcGluZ0FkZHJlc3MiOnsidGltZXN0YW1wIjoxNzUwNjY1NDA2NzA1LCJ0eXBlIjoicGFydGlhbC1sb2NhdGlvbiIsImdpZnRBZGRyZXNzIjpmYWxzZSwicG9zdGFsQ29kZSI6IlY1WiA5WjAiLCJkZWxpdmVyeVN0b3JlTGlzdCI6W3sibm9kZUlkIjoiMTEwNCIsInR5cGUiOiJERUxJVkVSWSIsInRpbWVzdGFtcCI6MTc1MDY2MTc2MzcyNywiZGVsaXZlcnlUaWVyIjpudWxsLCJzZWxlY3Rpb25UeXBlIjoiTFNfU0VMRUNURUQiLCJzZWxlY3Rpb25Tb3VyY2UiOiJJUF9TTklGRkVEX0JZX0xTIn1dLCJjaXR5IjoiVmFuY291dmVyIiwic3RhdGUiOiJCQyJ9LCJwb3N0YWxDb2RlIjp7InRpbWVzdGFtcCI6MTc1MDY2NTQwNjcwNSwiYmFzZSI6IlY1WiA5WjAifSwibXAiOltdLCJtcERlbFN0b3JlQ291bnQiOjAsInNob3dMb2NhbEV4cGVyaWVuY2UiOmZhbHNlLCJzaG93TE1QRW50cnlQb2ludCI6ZmFsc2UsIm1wVW5pcXVlU2VsbGVyQ291bnQiOjAsInZhbGlkYXRlS2V5IjoicHJvZDp2MzphZGRmY2RiYy04MjhlLTRjZjItOTJiYy0zMjk0M2ZiZmQ1OGQifQ==; userAppVersion=caweb-1.134.0-36c66ff8bec9d3214adcf2e2d56466ca4fb2fd72-6162053r; wmt.c=0; seqnum=4; vtc=ZRAOe7IAWfgzhdY2ruWlq0; bstc=ZRAOe7IAWfgzhdY2ruWlq0; xpa=-v6XR^|1QMX4^|90pdM^|9GfWA^|AXJ7n^|CJWNp^|IQtsA^|JuXPz^|asDyH^|cP5ay^|fFLYP^|kE1zy^|m1Puw^|mHdyO^|mn7jJ^|tMZ_K^|wDJGf; xpm=1%2B1750665406%2BZRAOe7IAWfgzhdY2ruWlq0~%2B0; exp-ck=-v6XR11QMX4390pdM1CJWNp2kE1zy3m1Puw1mHdyO1wDJGf1; xptwj=cp:f0119be8a268703808f4:xq4iN6wL3EG1Z7+9fZd0hAGb10Kv2iY2/svYTrkensTivXJDl4EgA5J2C+DjbCLJrjujEeeT6R4GtEQvGhKXVa09d+txtr/6eRZjRnCo6aX5Bibyq/jAVWQUUgan0eFPqrI9ShHa61qgW1d/TbtQq6LZkLlwizqmhYfzWDc=; uxcon=enforce=false^&p13n=true^&ads=true^&createdAt=1750665408769^&modifiedAt=; walmart.nearestPostalCode=V5Z9Z0; walmart.nearestLatLng="49.2476,-123.1234"; userSegment=50-percent; ak_bmsc=FF65250E3918719123B3287A3011F46C~000000000000000000000000000000~YAAQxzfLF1s6CpCXAQAALjHKmxwSKi7je5zuy0qmttf1MHkceqKb8H6Zp9f0OZxxkUXdYkEYnMLHs/Nyj/bqWJSk4DVZv8jVTsH1Yr88A5ynUWSK0dc+ISOoPX+f86dA8tbTmorSGO6TcFE3kHCGhfMLr05z9RvKHSCcwNSZ8kEsHu5X9CPeOF5k2GC1SW3FX8up8Gau3jKltOPWS7Gn534xBxWwXsuRqWjpqNlRT9umHIUAEszNkXoFepfgl501zurjFVcQyOu3vTEzl4ac9qbEAsU4JFyB95PnWHPRdYrYJpcjlZCGDuM1PUZyznOpvvEHd82NL7WkdR6MkbzNbxa92cP2lgXv5o9k6EIBa8leR4UF8k5vRzKOETyZXkWL2T3wi8Cn+CJ54UI=; bm_sv=451BD7B279F9B42F894062AA3D9307A0~YAAQxzfLF5NACpCXAQAANHTKmxxrRC0NwAfzTDJbeqbo+Jwt8u3/PeOYKaSp9uJrFtKcQJVeBOv8bFhhx/kmKaqcvcibGraJFTnLe5BICyj1hYXqD/9W5ZXkfupEigpZPhqyZL+d/1JPD7DBBZSy+s6FuPgi8+Nj6XsVkR2vCpJFsthgmbrNLDr90inmH33y3kKWrd6vjNc0GS0ZBpKJZbGfgCwd7koZC41YS3UQBQTtM0EyPnvhRR+etYtF+lae~1; _astc=195cdd9a6ae47b0ff0cdc8dc11880866; adblocked=true; ACID=addfcdbc-828e-4cf2-92bc-32943fbfd58d; TS0180da25=01a21c49d236b5f0fe9b111e38626ce09ec8ed8014bb4d9dabdf8cc76a0090597ece2faa63c0a56e13e9795f7fe638b53787c29c8e; TS01ea8d4c=01a21c49d236b5f0fe9b111e38626ce09ec8ed8014bb4d9dabdf8cc76a0090597ece2faa63c0a56e13e9795f7fe638b53787c29c8e; ak-ca-origin-route=legacy; ak_bmsc=08694F7C6C510A303800CC58A567D0C4~000000000000000000000000000000~YAAQh89YaH0own2XAQAAwO/RmxxtNV9wdUn8GAsT1UOGfkd+BCxn7nN+2fxcjX5L5PEOouR3ZZcbuJdH5sQEXA7HAlSvH7NSpF6xzZURZ7oFF73JUGoP8S+KQ54hkOCjh4PS3cWo5ePkaMhs8YjNepJ/tUhkQo5KLk5NE/fSsZMoUwCMG430v5ztoHfIIe/6hpJhz0JuPF1DlebbUg3qJoDqYiIqy8XNfJ3VrNPq0RDCTfXzYNcuH3svQOjXyXHk4Cdia1YG1iu3+U6SPDlUIqqgZ/qZMj10jP9nMxRv2aDy7D7eo3kix9FXA/6V34GomD6jjZz1lmJqeo7J7D5P6MolCuJ+0iCIORt7jA==; bm_sv=451BD7B279F9B42F894062AA3D9307A0~YAAQh89YaNFPxn2XAQAAS7zvmxw1W27n6qz+WTUmMpdXd8juA8k8aDEK6L0DHcH8PbtZXZw+RXl45xegbdn8kIgIqtVsGh+YOpPXlI2rnyPwlMDmJjmdho1VhVLCt5ZwoFxYcB0wJ0S1EJ1lUBW2IUWpb3aXhTd393b4KRDXAZBsteAMjHW4Hwi5gpEjmh5b6dRuI1RpFLwJySHLJKmdwXGvKm34qu1AXtrDvwysdRO7jSyZGvRtBjyHzhmOoODW~1; bstc=ZRAOe7IAWfgzhdY2ruWlq0; exp-ck=-v6XR^01QMX4^090pdM^09GfWA^0AXJ7n^0CJWNp^0IQtsA^0JuXPz^0asDyH^0cP5ay^0fFLYP^0kE1zy^0m1Puw^0mHdyO^0mn7jJ^0tMZ_K^0wDJGf1; seqnum=5; uxcon=enforce=false&p13n=true&ads=true&createdAt=1750665916281&modifiedAt=; vtc=ZRAOe7IAWfgzhdY2ruWlq0; wmt.c=0; xpa=-v6XR^|1QMX4^|90pdM^|9GfWA^|AXJ7n^|CJWNp^|IQtsA^|JuXPz^|asDyH^|cP5ay^|fFLYP^|kE1zy^|m1Puw^|mHdyO^|mn7jJ^|tMZ_K^|wDJGf; xpm=1%2B1750665406%2BZRAOe7IAWfgzhdY2ruWlq0~%2B0; TS010110a1=01a21c49d236b5f0fe9b111e38626ce09ec8ed8014bb4d9dabdf8cc76a0090597ece2faa63c0a56e13e9795f7fe638b53787c29c8e; TSe62c5f0d027=088498edc7ab2000dccb9c49bd96334f4e20339fd452e09b23591936d06d0b457ab812d6f2a05b6e08bd16a4f5113000b7cc9b09ece4cb9f23af34fe8fb4ddae157df1f02cbcc09a40725e6771e2553164c5e1c514b62c70419ea4e85602ce37; userSegment=10-percent; walmart.nearestLatLng="49.2476,-123.1234"; walmart.nearestPostalCode=V5Z9Z0',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=4",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }
        walmart_cookies = {
            #  "WM_SEC.AUTH_TOKEN": "MTAyOTYyMDE42%2Ft9gqnpwzPta%2FelwRGCFi7GC9jXAJptbyFn8s%2FDtHUgXqcvubMBEK2QjZq2Fy5HSAgN7ksqcddGItcBv5nLoVNSyTYfllYOeqg6lW6pEQqUy%2BihUWsXB58r5eePz348j8OFN4dileb20bpDLeCIlSFd%2FHsc7bnSe4%2BTLU2zbj3RQyEzpTh3Ol6Ny127bRz%2Bn56%2FKCTYpMJy5iCQ05U%2BsHyzLueJMVTnzRxthwochdeWRXS%2FVM7dhoO5fDBksK28pGd2w9VMvEOMsmi01MtA%2F8ecV0FVdXP9TaH3bXdQyOVLRsFnDZFL31FvI%2FZvIuBfh%2F0m9IovrIbS7h3MTVLstzOg7ZvF%2FUrOFw%2B6oLgUtF5Ul13vZDRHH7OGXUBvGtGizrutrvFTgI1u89cDHCU%2BVCCFU7YNy%2B%2B7Og%2FK1CpgYd8%3D",
            "auth": "MTAyOTYyMDE4DE6jyfPo1d0E2zZ4Qn248x49F9uxVXrhRGdlDiX7fOjOZgEmxAwCRz8VRqGCgVAl81SurlRcpR1%2FeQ8yCgUU%2BJhgXP897VOC97CDlGf0k1S7rww66Q8cUDNyc%2F3DSOaxj8OFN4dileb20bpDLeCIlSFd%2FHsc7bnSe4%2BTLU2zbj17CYdpegknYU0Zi4y2T9fCpUTATi2CsUm%2B03hZmSXOfn2Kw%2Fl4U8z%2BMCFULom2MUGWRXS%2FVM7dhoO5fDBksK28pGd2w9VMvEOMsmi01MtA%2Fwy6yd1WbYCmt0ZvUnNBajWGjRlKwaB3hGjglkYV8afcQ0x%2BtqZcZN2F9J5P8RFumktq03mxyRIb%2BsIQfpgZXiaYkViBJfVltOdZpQemsAY8UqOWoNqTXTPsacbfXQLAoyCFU7YNy%2B%2B7Og%2FK1CpgYd8%3D",
            "ACID": "dddfcdbc-828e-4cf2-92bc-32943fbfd58d",
            "hasACID": "true",
            "walmart.nearestPostalCode": postal_code,
            "wmt.c": "0",
            "walmart.nearestLatLng": "49.1234,-123.1234",
            "uxcon": "enforce=false^&p13n=true^&ads=true^&createdAt=1750665408769^&modifiedAt=",
            "ak_bmsc": "FF65250E3918719123B3287A3011F46C~000000000000000000000000000000~YAAQxzfLF1s6CpCXAQAALjHKmxwSKi7je5zuy0qmttf1MHkceqKb8H6Zp9f0OZxxkUXdYkEYnMLHs/Nyj/bqWJSk4DVZv8jVTsH1Yr88A5ynUWSK0dc+ISOoPX+f86dA8tbTmorSGO6TcFE3kHCGhfMLr05z9RvKHSCcwNSZ8kEsHu5X9CPeOF5k2GC1SW3FX8up8Gau3jKltOPWS7Gn534xBxWwXsuRqWjpqNlRT9umHIUAEszNkXoFepfgl501zurjFVcQyOu3vTEzl4ac9qbEAsU4JFyB95PnWHPRdYrYJpcjlZCGDuM1PUZyznOpvvEHd82NL7WkdR6MkbzNbxa92cP2lgXv5o9k6EIBa8leR4UF8k5vRzKOETyZXkWL2T3wi8Cn+CJ54UI=",
            "ak-ca-origin-route": "legacy",
            "DYN_USER_ID.ro": "425b274d-49d5-41b5-bbc9-66af2b60bec7",
            "bm_sv": "451BD7B279F9B42F894062AA3D9307A0~YAAQxzfLF5NACpCXAQAANHTKmxxrRC0NwAfzTDJbeqbo+Jwt8u3/PeOYKaSp9uJrFtKcQJVeBOv8bFhhx/kmKaqcvcibGraJFTnLe5BICyj1hYXqD/9W5ZXkfupEigpZPhqyZL+d/1JPD7DBBZSy+s6FuPgi8+Nj6XsVkR2vCpJFsthgmbrNLDr90inmH33y3kKWrd6vjNc0GS0ZBpKJZbGfgCwd7koZC41YS3UQBQTtM0EyPnvhRR+etYtF+lae~1",
            "_astc": "595cdd9f6fe47b0ff0cbc8dc11880866",
            "vtc": "ZRAOe7IAWfgzhdY2ruWlq0",
            "bstc": "ZRAOe7IAWfgzhdY2ruWlq0",
            "seqnum": "4",
            "X-Frame-Options": "SAMEORIGIN",
            "X-Gql-Status": "OK",
            "headerType": "whiteGM",
            "authDuration": '{"lat": "1739969327091000", "lt": "1739969327091000"}',
            "xpm": "1%2B1742269519%2B62E7E52A-8C33-4E14-810B-46225509222E~%2B5",
            "exp-ck": "8X9Qx1lL7zR1yPk5d1",
            "userSegment": "50-percent",
            "userAppVersion": "caweb-1.134.0-36c66ff8bec9d3214adcf2e2d56466ca4fb2fd72-6162053r",
            "TS010110a1": "0151d97a5649488ee95f03fddee8772471d754fb077826fed6c2f923a5dfe20b4de421f7ae1b6cefad30abe22ab08bc367c4a23057",
            "TS01ea8d4c": "0151d97a5649488ee95f03fddee8772471d754fb077826fed6c2f923a5dfe20b4de421f7ae1b6cefad30abe22ab08bc367c4a23057",
            "TS0180da25": "0151d97a5649488ee95f03fddee8772471d754fb077826fed6c2f923a5dfe20b4de421f7ae1b6cefad30abe22ab08bc367c4a23057",
            "TSe62c5f0d027": "089fde974cab200056a15ddfae1437dfcd750532c8a88b242074b3c86ce84ddb4ef1e783299becc80891543a581130007e37d92811e9a9fb38bf6e6cb6742f143c7cb7e99ce613d634bc2746dca968ea7a00101cfd2204291442e2f4bb11aa5a",
            "TS01f0f358": "01cfee4702c15f491121d6d079ebc09ed921b8ccca76e7a6969b188fac194b14dd5773b5a60bb3fe9909a4f93a33843edfd0fb0501",
            "pxcts": "fe36dcee-c317-11ef-a695-5cb4b5f45bad",
            "wm_route_based_language": "en-CA",
            "LT": "1749083393504",
            "locDataV3": "eyJpc0RlZmF1bHRlZCI6ZmFsc2UsImlzRXhwbGljaXQiOmZhbHNlLCJpbnRlbnQiOiJERUxJVkVSWSIsInBpY2t1cCI6W3sibm9kZUlkIjoiMTEwNCIsImRpc3BsYXlOYW1lIjoiVkFOQ09VVkVSLCBCQyIsImFkZHJlc3MiOnsicG9zdGFsQ29kZSI6IlY1TSAyRzciLCJhZGRyZXNzTGluZTEiOiIzNTg1IEdSQU5EVklFVyBIV1kiLCJjaXR5IjoiVmFuY291dmVyIiwic3RhdGUiOiJCQyIsImNvdW50cnkiOiJDQSJ9LCJnZW9Qb2ludCI6eyJsYXRpdHVkZSI6NDkuMjU5MjQ2LCJsb25naXR1ZGUiOi0xMjMuMDI3NDQ2fSwic2NoZWR1bGVkRW5hYmxlZCI6dHJ1ZSwidW5TY2hlZHVsZWRFbmFibGVkIjpmYWxzZSwic3RvcmVIcnMiOiIwNzowMC0yMzowMCIsInN1cHBvcnRlZEFjY2Vzc1R5cGVzIjpbIlBJQ0tVUF9DVVJCU0lERSIsIlBJQ0tVUF9JTlNUT1JFIl0sInRpbWVab25lIjoiUFNUIiwic3RvcmVCcmFuZEZvcm1hdCI6IldhbG1hcnQgU3VwZXJjZW50ZXIiLCJzZWxlY3Rpb25UeXBlIjoiTFNfU0VMRUNURUQifV0sInNoaXBwaW5nQWRkcmVzcyI6eyJsYXRpdHVkZSI6NDkuMjQ3NDU4MiwibG9uZ2l0dWRlIjotMTIzLjEyMTU0MTIsInBvc3RhbENvZGUiOiJWNVogOVowIiwiY2l0eSI6IlZhbmNvdXZlciIsInN0YXRlIjoiQkMiLCJjb3VudHJ5Q29kZSI6IkNBIiwibG9jYXRpb25BY2N1cmFjeSI6ImxvdyIsImdpZnRBZGRyZXNzIjpmYWxzZX0sImFzc29ydG1lbnQiOnsibm9kZUlkIjoiMTEwNCIsImRpc3BsYXlOYW1lIjoiVkFOQ09VVkVSLCBCQyIsImFjY2Vzc1BvaW50cyI6W3siYWNjZXNzVHlwZSI6IkRFTElWRVJZX0FERFJFU1MifV0sInN1cHBvcnRlZEFjY2Vzc1R5cGVzIjpbIkRFTElWRVJZX0FERFJFU1MiXSwiaW50ZW50IjoiREVMSVZFUlkifSwiaW5zdG9yZSI6ZmFsc2UsImRlbGl2ZXJ5Ijp7Im5vZGVJZCI6IjExMDQiLCJkaXNwbGF5TmFtZSI6IlZBTkNPVVZFUiwgQkMiLCJhZGRyZXNzIjp7InBvc3RhbENvZGUiOiJWNU0gMkc3IiwiYWRkcmVzc0xpbmUxIjoiMzU4NSBHUkFORFZJRVcgSFdZIiwiY2l0eSI6IlZhbmNvdXZlciIsInN0YXRlIjoiQkMiLCJjb3VudHJ5IjoiQ0EifSwiZ2VvUG9pbnQiOnsibGF0aXR1ZGUiOjQ5LjI1OTI0NiwibG9uZ2l0dWRlIjotMTIzLjAyNzQ0Nn0sInNjaGVkdWxlZEVuYWJsZWQiOmZhbHNlLCJ1blNjaGVkdWxlZEVuYWJsZWQiOmZhbHNlLCJhY2Nlc3NQb2ludHMiOlt7ImFjY2Vzc1R5cGUiOiJERUxJVkVSWV9BRERSRVNTIn1dLCJpc0V4cHJlc3NEZWxpdmVyeU9ubHkiOmZhbHNlLCJzdXBwb3J0ZWRBY2Nlc3NUeXBlcyI6WyJERUxJVkVSWV9BRERSRVNTIl0sInRpbWVab25lIjoiQW1lcmljYS9WYW5jb3V2ZXIiLCJzdG9yZUJyYW5kRm9ybWF0IjoiV2FsbWFydCBTdXBlcmNlbnRlciIsInNlbGVjdGlvblR5cGUiOiJMU19TRUxFQ1RFRCJ9LCJpc2dlb0ludGxVc2VyIjpmYWxzZSwibXBEZWxTdG9yZUNvdW50IjowLCJyZWZyZXNoQXQiOjE3NTA2ODcwMDY3MDYsInZhbGlkYXRlS2V5IjoicHJvZDp2MzphZGRmY2RiYy04MjhlLTRjZjItOTJiYy0zMjk0M2ZiZmQ1OGQifQ",
        }

        response = requests.get(
            self.walmart_api_url + walmart_api_search_path,
            headers=walmart_headers,
            cookies=walmart_cookies,
        )

        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    # Set Walmart store by ID
    def set_store_walmart(self, store_id):
        self.walmart_store_number = store_id

    # Query Walmart search by store ID
    def query_walmart(self):
        walmart_api_search_path = (
            "/orchestra/snb/graphql/search?query="
            + self.search_query
            + "&page=1&displayGuidedNav=true&additionalQueryParams=%7BisMoreOptionsTileEnabled%3Dtrue%7D"
        )

        walmart_headers = {
            "X-O-Platform-Version": "22.41.3",
            "X-Px-Authorization": "3",
            "User-Agent": "WMT1H-CA/22.41.3 iOS/16.2",
            "X-O-Bu": "WALMART-CA",
            "X-Apollo-Operation-Name": "getPreso",
            "Wm_qos.correlation_id": "7F63DE7D-9729-401B-B50C-5F37D19EDF70",
            "X-Wm-Vid": "8B95354D-6FE8-4F18-904F-4ED9AE73EE24",
            "Caching-Operation-Name": "MobileSearchPage",
            "Wm_mp": "true",
            "X-O-Mart": "B2C",
            "X-Enable-Server-Timing": "1",
            "X-O-Tp-Phase": "tp5",
            "X-O-Platform": "ios",
            "X-O-Device": "iPhone13,2",
            "X-O-Segment": "oaoh",
            "X-Px-Original-Token": "3:5d8aff4b639c9d6ce96dd8979d4fe3dcd702e0065a2bd62cd333f54ff84dea7b:RqmKg11hDTod8tEEjlLZe0bD60p1bfA2AyTXqgxDq7PHL1scy+gxTfQQvDw75aV2r5FlMAhiU72mS3KDqt6Snw==:1000:S16G4ZqvF0uGnL86ueNz+zjsQtuSL/L5ClLAOgcs619p8vQaaxCwtMIkOYXzVo9QBfvtGxq8YTz44TPS3uSV4ljjScfS/zDaAUvTHrNONp1Tvnyqb8vW4qmGhYrrALtx52iK6VoahSu+fzdb5kho5mWKtB8C5McafISt6ZFn7zOM5R+FrpO/7WbA1LB0sbqf7Vfc4RBk2hkKs2s03LIQSw==",
            "Accept-Language": "en-CA,en-US;q=0.9,en;q=0.8",
            "X-Latency-Trace": "1",
            "X-O-Device-Id": "850FEBFD-9B4E-44E9-BD70-68FBFF6541AB",
            "Traceparent": "00-7f4211a907253d32944c9f52c149dec6-999f6efa5c49815d-00",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Wm-Client-Name": "glass",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "X-Wm-Sid": "C1917B15-633C-4C83-8A63-510770593E27",
        }

        walmart_cookies = {
            "WM_SEC.AUTH_TOKEN": "MTAyOTYyMDE4Fil%2FreSPGCFIzeU859bxShtSv%2Fj8OoHIkjOZqg7cKKtzQIdpmFzg%2FSyfAt0YdIIXdfhWR7CXf0l5Qc6A6tDeoeX5zjz2fyw8ykcDzcOFmVZ2DNn288pSUIbbHwiiE18Gj8OFN4dileb20bpDLeCIlSFd%2FHsc7bnSe4%2BTLU2zbj3qFXCDZhTgwdgz58vBPqJGmkxZqbhaRFIJ5UKTqNuDfuKxzjTI9b2Ox5ET5ay4mObb%2FSoGFgAYL9DGZ8K45WCXM%2FFHGZ2dCNmxWrdkwqEKrunqHP%2BELc1vcoMIfiAZWUoadqmNrmJhxgd2bNohwCkPG1I7uGmt7s6IA85gZ1vL8Irw4%2B1G54bxExI%2FfXW%2FZG8dDNIfTntJm6bUfn07FPjedimhYhzdDILh5vFDkGRcQEr1eX9YGQ0laieVMoEr348%3D",
            "deliveryCatchment": self.walmart_store_number,
            # "walmart.nearestPostalCode": "V4G1N4",
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
        walmart_request = requests.post(
            self.walmart_api_url + walmart_api_search_path,
            json=walmart_data_body,
            headers=walmart_headers,
            cookies=walmart_cookies,
        )

        return walmart_request.json()
