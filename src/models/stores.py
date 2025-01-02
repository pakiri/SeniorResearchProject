from app import db

class Stores(db.Model):
    store_id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    store_name = db.Column(db.String(20), nullable=False, unique=False)
    url = db.Column(db.String(150), nullable=False, unique=True)

    def __repr__(self):
        return f"Store Name : {self.store_name}, URL: {self.url}"
