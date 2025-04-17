from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import requests
from datetime import datetime
import re
from emailsender import sendEmail

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

class User(Base):
    __tablename__ = "Users"
    id = Column(Integer, primary_key=True)
    username = Column(String(150), nullable=False, unique=True)
    email = Column(String(120), nullable=False, unique=True)
    password = Column(String(150), nullable=False)
    role = Column(String(5), nullable=False)

class Alerts(Base):
    __tablename__ = "Alerts"
    alert_id = Column(Integer, primary_key=True)
    item_name = Column(String(50), unique=False)
    user_id = Column(Integer, ForeignKey('Users.id'))
    store_id = Column(Integer, ForeignKey('Stores.store_id'))
    zipcode = Column(String(5), unique=False)
    price_threshold = Column(Float, unique=False)
    timestamp = Column(String(150), nullable=False)
    user = relationship('User', backref='alert')
    store = relationship('Stores', backref='alert')

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
        print(f"Refreshed information in the database for {store.store_name}, {USER_ZIPCODE}\n")
    
    print("="*50+"\n")

    alerts = session.query(Alerts).all()
    for alert in alerts:
        searchTerm, priceThreshold = alert.item_name, alert.price_threshold
        entries = session.query(PricingInfo).filter_by(store_id=alert.store.store_id, zipcode=alert.zipcode)
        for entry in entries:
            if searchTerm in entry.item_name and (currentPrice := entry.price) < priceThreshold:
                username = alert.user.username
                print(f"Sending email to {username}")
                htmlContent = f"""\
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Price Alert - GroceryCheck</title>
                        <style>
                            body {{
                                font-family: Arial, sans-serif;
                                background-color: #f8f9fa;
                                margin: 0;
                                padding: 0;
                            }}
                            .container {{
                                max-width: 600px;
                                margin: 20px auto;
                                background: #ffffff;
                                padding: 20px;
                                border-radius: 10px;
                                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                                text-align: center;
                            }}
                            h1 {{
                                color: #2c3e50;
                            }}
                            .content {{
                                text-align: left;
                                font-size: 16px;
                                color: #333;
                            }}
                            .highlight {{
                                font-weight: bold;
                                color: #0d6efd;
                            }}
                            .cta-button {{
                                display: inline-block;
                                margin: 20px 0;
                                padding: 12px 20px;
                                background-color: #0d6efd;
                                color: #ffffff !important;
                                text-decoration: none;
                                font-size: 18px;
                                border-radius: 5px;
                                border: none;
                                cursor: pointer;
                            }}
                            .cta-button:hover {{
                                background-color: #218838;
                            }}
                            .footer {{
                                font-size: 14px;
                                color: #777;
                                margin-top: 20px;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>🚨 Price Alert Triggered!</h1>
                            <div class="content">
                                <p>Hi { username },</p>
                                <p>Great news! One of your GroceryCheck alerts just triggered:</p>
                                <ul>
                                    <li><strong>Item:</strong> <span class="highlight">{ alert.item_name }</span></li>
                                    <li><strong>Store:</strong> <span class="highlight">{ alert.store.store_name }</span></li>
                                    <li><strong>ZIP Code:</strong> <span class="highlight">{ alert.zipcode }</span></li>
                                    <li><strong>Your Price Threshold:</strong> <span class="highlight">${ '%0.2f' % priceThreshold }</span></li>
                                    <li><strong>Current Price:</strong> <span class="highlight">${ '%0.2f' % currentPrice }</span></li>
                                </ul>
                                <p>Click below to view the latest deal and see more details:</p>
                                <p><a href="http://localhost:5000/alerts" class="cta-button">View My Alerts</a></p>
                            </div>
                            <div class="footer">
                                <p>Happy saving!<br><strong>The GroceryCheck Team</strong></p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                sendEmail(username, alert.user.email, f"Deal found! {alert.item_name} at {alert.store.store_name} is below your price threshold!", htmlContent)
