from .base import db, BaseModel

class UserPreference(BaseModel):
    __tablename__ = 'user_preferences'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    user_name = db.Column(db.String(64), nullable=False)
    user_title = db.Column(db.String(64), nullable=False)
    user_measurement = db.Column(db.String(64), nullable=False)
    user_bio = db.Column(db.Text, nullable=True)
    user_language = db.Column(db.String(64), nullable=False)
    user_location_full = db.Column(db.String(64), nullable=False)
    user_location_country = db.Column(db.String(3), nullable=True)

    def __repr__(self):
        return f"<UserPreference {self.user_name} for User {self.user_id}>"
