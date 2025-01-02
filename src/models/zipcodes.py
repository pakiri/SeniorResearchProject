from app import db

class ZipCode(db.Model):
    __tablename__ = "US_Zip_Codes"
    zipcode = db.Column(db.String(5), primary_key=True, nullable=False, unique=True)
    city = db.Column(db.String(50), nullable=False, unique=False)
    state = db.Column(db.String(2), nullable=False, unique=False)

    def __repr__(self):
        return f"Location: {self.zipcode}, {self.city}, {self.state}"
