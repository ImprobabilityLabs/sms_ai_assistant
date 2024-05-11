from .base import db, BaseModel

class User(BaseModel):
    __tablename__ = 'users'

    provider_id = db.Column(db.String(255), primary_key=True)
    stripe_customer_id = db.Column(db.String(255), index=True, nullable=True)  # Index this for faster lookups once populated
    provider_name = db.Column(db.String(16), nullable=False)  # 'google', 'apple', 'microsoft'
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=True)
    profile_pic = db.Column(db.String(255), nullable=True)  # URL to the profile picture

    def __repr__(self):
        return f"<User {self.email}>"
