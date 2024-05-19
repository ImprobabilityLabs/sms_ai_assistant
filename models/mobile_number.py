from .base import db, BaseModel
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.dialects.mysql import BIGINT
import phonenumbers

class MobileNumber(BaseModel):
    __tablename__ = 'mobile_numbers'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    country_code = db.Column(INTEGER(unsigned=True), nullable=False)
    mobile_number = db.Column(BIGINT(unsigned=True), nullable=False)

    def __repr__(self):
        # Construct the full international number
        full_number = f"+{self.country_code}{self.mobile_number}"
        
        # Parse the number using phonenumbers
        parsed_number = phonenumbers.parse(full_number, None)
        
        # Format the number using international format
        formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        
        # Get the country name from the country code
        country_name = phonenumbers.geocoder.description_for_number(parsed_number, "en")
        
        # Use country abbreviation (ISO 3166-1 alpha-2)
        country_abbr = phonenumbers.region_code_for_number(parsed_number)
        
        return f"<MobileNumber {formatted_number} ({country_name}, {country_abbr})>"

