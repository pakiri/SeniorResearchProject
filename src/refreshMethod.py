from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base
import requests
from datetime import datetime
import re

USER_ZIPCODE = "22312" # hard code for now, but later loop through all zip codes in the database and refresh for each

categories = [r"\bapples?\b(?!\s*sauce)",
              r"grape(?!fruit)",
              r"onion(?! ring)",
              r"oranges",
              r"tomato(?! )"]

Base = declarative_base() # used a declarative base instead of a db in order to not run the Flask app

class Stores(Base):
    __tablename__ = "Stores"
    store_id = Column(Integer, primary_key=True, nullable=False, unique=True)
    store_name = Column(String(20), nullable=False, unique=False)

    def __repr__(self):
        return f"Store Name : {self.store_name}"

class PricingInfo(Base):
    __tablename__ = "Pricing_Info"
    id = Column(Integer, primary_key=True, nullable=False, unique=True)
    product_id = Column(Integer, unique=False)
    item_name = Column(String(50), unique=False)
    zipcode = Column(String(5), unique=False)
    unit = Column(String(20), unique=False)
    store_id = Column(Integer, unique=False)
    price = Column(Float, unique=False)
    created_date = Column(String(20), unique=False)
    image_url = Column(String(75), unique=False)
    pre_price_text = Column(String(20), unique=False)
    post_price_text = Column(String(20), unique=False)

    def __repr__(self):
        return f"Product ID: {self.product_id}, Item Name: {self.item_name}, Store ID: {self.store_id}, Zip Code: {self.zipcode}, Price: {self.price}, Unit: {self.unit}, Date of Creation: {self.created_date}, Image URL: {self.image_url}, Pre Price Text: {self.pre_price_text}, Post Price Text: {self.post_price_text}"

engine = create_engine('sqlite:///instance/SRdata.db')
Session = sessionmaker(bind=engine)

with Session() as session:
    for store_id in range(1, 20): # currently 19 stores in the Stores data table
        store = session.get(Stores, store_id)

        # 2. data extraction from JSON
        url = f"https://backflipp.wishabi.com/flipp/items/search?locale=en-us&postal_code={USER_ZIPCODE}&q={store.store_name}"
        response = requests.get(url)

        if response.status_code == 200: # if request was successful
            data = response.json()
            items = data["items"]

            session.query(PricingInfo).filter_by(store_id=store_id, zipcode=USER_ZIPCODE).delete() # delete all instances in the database where the store ID and zip code match

            print(f"Deleted data for {store.store_name}, {USER_ZIPCODE}")
        else:
            print(f"Error: {response.status_code}")

        # 3. saving data in database
        for item in items:
            if "_L2" in item and item["_L2"] == "Food Items" and item["current_price"]:
                newPricingInfo = PricingInfo()
                newPricingInfo.image_url = item["clean_image_url"]
                newPricingInfo.item_name = item["name"]
                newPricingInfo.store_id = store_id
                newPricingInfo.zipcode = USER_ZIPCODE
                newPricingInfo.price = item["current_price"]
                newPricingInfo.pre_price_text = item["pre_price_text"]
                newPricingInfo.post_price_text = item["post_price_text"]
                newPricingInfo.created_date = datetime.now().strftime("%Y-%m-%d")

                for idx, rString in enumerate(categories):
                    if re.search(rString, item["name"], re.IGNORECASE):
                        newPricingInfo.product_id = idx+1
                    
                session.add(newPricingInfo)
        
        session.commit()
        print(f"Refreshed information in the database for {store.store_name}, {USER_ZIPCODE}")
