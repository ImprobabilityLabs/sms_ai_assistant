from .base import db, BaseModel
from datetime import datetime

class Subscription(BaseModel):
    __tablename__ = 'subscriptions'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_customer_id = db.Column(db.String(255), nullable=True)
    stripe_plan_id = db.Column(db.String(255), nullable=False)
    stripe_product_id = db.Column(db.String(255), nullable=False)
    stripe_subscription_id = db.Column(db.String(255), nullable=False)
    current_period_start = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)
    last_payment_amount = db.Column(db.Float, nullable=True)  
    last_payment_date = db.Column(db.DateTime, nullable=True)
    twillio_number = db.Column(db.String(32), nullable=True)
    twillio_number_sid = db.Column(db.String(64), unique=True, nullable=True)
    status = db.Column(db.String(64), nullable=False)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    billing_error = db.Column(db.Boolean, default=False, nullable=False)
    referrer = db.Column(db.String(64), nullable=True)

    def __repr__(self):
        return f"<Subscription {self.stripe_plan_id} for User {self.user_id}>"
