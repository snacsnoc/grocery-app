This document serves to document the web architecture of popular Canadian grocery stores.


# President's Choice (Loblaws)
After attacks on their member point system in 2019, President's Choice rebuilt their public API endpoint with added security (basic authentication hah).
Subsidiary websites and the mobile app query the same endpoint, and is used from querying products to user authentication.

Endpoint: `api.pcexpress.ca`


`realcanadiansuperstore.ca` allows users to set their location and schedule grocery pick up. [The page](https://www.realcanadiansuperstore.ca/store-locator?type=store) uses an embedded Google Map to display store locations. 
The PC Express mobile app queries a 3rd party service, Bullseye Locations, to display store locations. With the public API key, we are able to query locations:

Endpoint: `ws2.bullseyelocations.com/RestSearch.svc/DoSearch2`

# Save-On-Foods 
Save-On-Foods started offering an online grocery pickup service around late 2019/2020

Endpoint: `storefrontgateway.saveonfoods.com/api`

To query stores we can send a GET request to: `https://storefrontgateway.saveonfoods.com/api/near/LATITUDE/LONGITUDE/STORERADIO/30/stores?shoppingModeId=11111111-1111-1111-1111-111111111111`

I am unsure what the third parameter does, set to 30 in the above example.

Result: https://gist.github.com/snacsnoc/ee0c2f3595ec652e1e282ec2ca8037a1