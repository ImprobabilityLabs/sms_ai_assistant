from .base import db, BaseModel

class History(BaseModel):
    __tablename__ = 'chat_history'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    sender = db.Column(db.String(64), nullable=False)  # Renamed 'from' to 'sender' to avoid keyword conflict
    message = db.Column(db.Text, nullable=False)  # Using Text for large amounts of text

    def __repr__(self):
        return f"<History from {self.sender}>"
