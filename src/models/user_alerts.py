from app import db

class UserAlert(db.Model):
    __tablename__ = 'User_Alerts'

    alert_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, nullable=False)
    category = db.Column(db.String)
    store_id = db.Column(db.Integer, db.ForeignKey('Stores.STORE_ID'))
    threshold_price = db.Column(db.Float, nullable=False)
    zipcode = db.Column(db.String, db.ForeignKey('US_Zip_Codes.ZIPCODE'), nullable=False)
    created_date = db.Column(db.String, default=db.func.current_timestamp())
    created_by = db.Column(db.String)
    modified_date = db.Column(db.String)
    modified_by = db.Column(db.String)

    def __repr__(self):
        return f"<UserAlert for {self.username} - ${self.threshold_price} in {self.zipcode}>"
