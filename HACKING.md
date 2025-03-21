This document serves to document the web architecture of popular Canadian grocery stores.


# President's Choice (Loblaws)
After attacks on their member point system in 2019, President's Choice rebuilt their public API endpoint with added security (basic authentication hah).
Subsidiary websites and the mobile app query the same endpoint, and is used from querying products to user authentication.

__Endpoint:__ `api.pcexpress.ca`

__Versioned API__

__Brand selector:__ `superstore`, `rass` (Atlantic), `nofrills`, `independent`

We can use the same endpoint to query Shoppers Drug Mart (`sdm`), and all other brands, by using the store id handle.

`realcanadiansuperstore.ca` allows users to set their location and schedule grocery pick up. [The page](https://www.realcanadiansuperstore.ca/store-locator?type=store) uses an embedded Google Map to display store locations. 


The PC Optimum mobile app queries a 3rd party service, Bullseye Locations, to display store locations. With the public API key, we are able to query locations:

__Endpoint:__ `ws2.bullseyelocations.com/RestSearch.svc/DoSearch2`

__URL params:__
`&CategoryIds=93204%2C93252`

`93204` = Superstore

`93252` = Independant Grocery, Shoppers Drugmart, ??? unknown others

# Save-On-Foods 
Save-On-Foods started offering an online grocery pickup service around late 2019/2020

__Endpoint:__ `storefrontgateway.saveonfoods.com/api`

To query stores we can send a GET request to: `https://storefrontgateway.saveonfoods.com/api/near/LATITUDE/LONGITUDE/STORERADIO/30/stores?shoppingModeId=11111111-1111-1111-1111-111111111111`

I am unsure what the third parameter does, set to 30 in the above example.

Result: https://gist.github.com/snacsnoc/ee0c2f3595ec652e1e282ec2ca8037a1

# Safeway Foods
Safeway is just starting with online grocery ordering, as their service is only available in the Greater Toronto Area, the Greater Montreal Area, Ottawa, and Quebec City.
There is only one API endpoint, with no location selection (national pricing?)

__Endpoint:__ `voila.ca/api`

__Versioned API__

GET request for suggested grocery items:
```commandline
curl -i -s -k -X $'GET' \
    -H $'Host: voila.ca' -H $'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"96\"' -H $'Accept: application/json; charset=utf-8' -H $'Client-Route-Id: ec43b74a-384f-41b5-98b3-bdec2473e2ef' -H $'Sec-Ch-Ua-Mobile: ?0' -H $'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36' -H $'Sec-Ch-Ua-Platform: \"macOS\"' -H $'Sec-Fetch-Site: same-origin' -H $'Sec-Fetch-Mode: cors' -H $'Sec-Fetch-Dest: empty' -H $'Referer: https://voila.ca/?utm_campaign=landingpage&utm_medium=referral&utm_source=voilabysafeway&utm_content=banner_cta' -H $'Accept-Encoding: gzip, deflate' -H $'Accept-Language: en-US,en;q=0.9' \
    -b $'language=en-CA; VISITORID=NzEyMmMzZTEtOTYzNy00MmIwLWI2NTAtNjY0NjBlZWVhOTVjOjE2NzAyMzA1NDA4NzA=; global_sid=PeQWtjZMRSVlTAPoFZAYLyLO31oKmIg5x9XdLwvJC52HdlvMBn42LOrjgegu_aVTaaUr9xkZuXWExRa6SfxKQc9yP6FbiXXk; _gcl_au=1.1.1551442977.1670230542' \
    $'https://voila.ca/api/v2/search/suggestions'
```
Result:
```commandline
["Eggs","Milk","Fruit","Chicken","Beef","Crackers","Cheese","Butter","Cucumber","Celery","Bread","Potatoes","Toilet Paper","Apples","Juice","Cream Cheese","Dog Food","Mushrooms","Sugar","Carrots","Sour Cream","Ice Cream","Onion","Pork","Oranges","Tomatoes","Avocado","Oat Milk"]
```

# Walmart
Walmart has a REST API for web just like the previous grocers and not much surprise here.
Unfortunately the devs at Walmart are smart enough to add anti-bot measures to reduce automated requests (aka this project...)
This project has been running successfully for 1yr+ so it's safe to say this API can be hit without being....blocked.

__Endpoint:__ `walmart.ca/api`

Searching for stores given a postal code or address is done like so:
```commandline
curl -i -s -k -X $'GET' \
    -H $'Host: www.walmart.ca' -H $'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"96\"' -H $'Sec-Ch-Ua-Mobile: ?0' -H $'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36' -H $'Sec-Ch-Ua-Platform: \"macOS\"' -H $'Accept: */*' -H $'Sec-Fetch-Site: same-origin' -H $'Sec-Fetch-Mode: cors' -H $'Sec-Fetch-Dest: empty' -H $'Referer: https://www.walmart.ca/en/stores-near-me' -H $'Accept-Encoding: gzip, deflate' -H $'Accept-Language: en-US,en;q=0.9' \
    -b $'Sec-Ch-Ua: \" Not A;Brand\";v=\"99\", \"Chromium\"; v=\"96\"' \
    $'https://www.walmart.ca/en/stores-near-me/api/searchStores?singleLineAddr=t3b1h4'
```

Result: https://gist.github.com/snacsnoc/ea71174078ed983122847a1e9389903c

Jumping into the mobile app, we can see that they are actually sending a GraphQL request. This allows searching to be much more powerful.

__Endpoint:__ `walmart.ca/orchestra/snb/graphql/search`

__URL params:__
```commandline
?query=carrots&page=1&displayGuidedNav=true&additionalQueryParams=%7BisMoreOptionsTileEnabled%3Dtrue%7D
```
Result: https://gist.github.com/snacsnoc/c8d09bd8b4811fef899899849925d9bb

You can search by lat/long + postal code or by store ID by setting the appropriate cookies.
```json
{
            "deliveryCatchment": self.walmart_store_number,
            "walmart.nearestPostalCode": "V4G1N4",
            "defaultNearestStoreId": self.walmart_store_number,
}
```