from app import db

class Products(db.Model):
    product_id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    product_name = db.Column(db.String(20), nullable=False, unique=False)
    description = db.Column(db.String(300), unique=False)

    def __repr__(self):
        return f"Product Name : {self.product_name}, Description: {self.description}"
