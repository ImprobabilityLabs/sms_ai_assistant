from .base import db, BaseModel
from sqlalchemy.dialects.mysql import INTEGER  

class MobileNumber(BaseModel):
    __tablename__ = 'mobile_numbers'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    country_code = db.Column(INTEGER(unsigned=True), nullable=False)
    mobile_number = db.Column(INTEGER(unsigned=True), nullable=False)

    def __repr__(self):
        full_number = f"+{self.country_code} ({self.area_code}) {self.mobile_number}"
        return f"<MobileNumber {full_number}>"
