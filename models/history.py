from .base import db, BaseModel

class History(BaseModel):
    __tablename__ = 'chat_history'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    message_sid = db.Column(db.Text, nullable=False)  # Twilio SID for the message
    direction = db.Column(db.String(10), nullable=False)  # 'inbound' or 'outbound'
    from_number = db.Column(db.String(32), nullable=False)
    to_number = db.Column(db.String(32), nullable=False)
    body = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=True)

    def __repr__(self):
        return f"<History from {self.from_number} to {self.to_number}>"
