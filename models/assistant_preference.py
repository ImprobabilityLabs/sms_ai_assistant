from .base import db, BaseModel

class AssistantPreference(BaseModel):
    __tablename__ = 'assistant_preferences'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    assistant_name = db.Column(db.String(32), nullable=False)
    assistant_origin = db.Column(db.String(32), nullable=False)
    assistant_gender = db.Column(db.String(16), nullable=False)
    assistant_personality = db.Column(db.String(16), nullable=False)
    assistant_response_style = db.Column(db.String(16), nullable=False)
    assistant_demeanor = db.Column(db.String(16), nullable=False)
    assistant_attitude = db.Column(db.String(16), nullable=False)

    def __repr__(self):
        return f"<AssistantPreference {self.assistant_name} for User {self.user_id}>"
