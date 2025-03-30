import requests

storesSet = ["Lidl", "Food Lion", "Harris Teeter", "Giant Food", "Grocery Outlet", "Yes! Organic Market", "ALDI", "Shoppers", "Sprouts Farmers Market", "Wegman's", "Target", "Safeway", "Global Food", "H Mart", "Lotte Plaza Market", "Costco", "Restaurant Depot", "Weis Markets", "Dollar General"]

zipcode = "22312"
storeName = "Giant Food"

url = f"https://backflipp.wishabi.com/flipp/items/search?locale=en-us&postal_code={zipcode}&q={storeName}"
response = requests.get(url)

if response.status_code == 200: # if request was successful
    data = response.json()
    items = data["items"]
else:
    print(f"Error: {response.status_code}")

for item in items:
    if "_L2" in item and item["_L2"] == "Food Items":
        print(item["clean_image_url"], item["name"], item["pre_price_text"], item["current_price"], item["post_price_text"], item["valid_to"])

