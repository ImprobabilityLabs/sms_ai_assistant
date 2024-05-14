from flask import Flask, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session
import os
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY, SQLALCHEMY_DATABASE_URI, STRIPE_API_KEY, MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, MICROSOFT_AUTHORIZATION_URL, MICROSOFT_TOKEN_URL, MICROSOFT_CLIENT_SECRET_ID, MICROSOFT_REDIRECT_URI
from flask import request
import requests
from werkzeug.middleware.proxy_fix import ProxyFix
import stripe


stripe.api_key = STRIPE_API_KEY 
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY 
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI 
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
db = SQLAlchemy(app)

GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

client = WebApplicationClient(GOOGLE_CLIENT_ID)

@app.route("/authorize/apple")
def authorize_apple():
    # Apple-specific OAuth configuration and redirect
    pass


@app.route("/authorize/microsoft")
def authorize_microsoft():
    client = OAuth2Session(MICROSOFT_CLIENT_ID, scope=["openid", "profile", "email"], redirect_uri=url_for("microsoft_callback", _external=True, _scheme='https'))
    uri, state = client.authorization_url(MICROSOFT_AUTHORIZATION_URL)
    return redirect(uri)


@app.route("/authorize/microsoft/callback")
def microsoft_callback():
    client = OAuth2Session(MICROSOFT_CLIENT_ID, scope=["openid", "profile", "email"], redirect_uri=url_for("microsoft_callback", _external=True, _scheme='https'))
    token = client.fetch_token(MICROSOFT_TOKEN_URL, client_secret=MICROSOFT_CLIENT_SECRET, authorization_response=request.url)
    user_info = client.get("https://graph.microsoft.com/oidc/userinfo").json()
    provider_id = user_info.get("sub")
    print(user_info)
    # Create a new user in the database if it doesn't exist
    user_name = user_info.get("name")
    if not user_name:
        user_name = user_info.get("givenname") + " " + user_info.get("familyname")
    user = db.session.get(User, provider_id)
    if not user:
        # Create a Stripe customer
        stripe_customer = stripe.Customer.create(
            email=user_info.get("email"),
            name=user_name,
            description="Customer for {}".format(user_info.get("email")),
        )
        user = User(
            provider_id=provider_id,
            email=user_info.get("email"),
            name=user_name,
            provider_name='microsoft',  # Set the provider as 'microsoft'
            profile_pic=user_info.get("picture", None),  # Use the 'picture' field from Microsoft, if available
            stripe_customer_id=stripe_customer.id  # Initialize as None; update when integrating with Stripe
        )
        db.session.add(user)
        db.session.commit()
    session["provider_id"] = provider_id
    return redirect(url_for("protected"))


@app.route("/authorize/google")
def authorize_google():
    client = OAuth2Session(GOOGLE_CLIENT_ID, scope=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"], redirect_uri=url_for("callback", _external=True, _scheme='https'))
    uri, state = client.authorization_url(GOOGLE_AUTHORIZATION_URL)
    return redirect(uri)


@app.route("/authorize/google/callback")
def callback():
    client = OAuth2Session(GOOGLE_CLIENT_ID, scope=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"], redirect_uri=url_for("callback", _external=True, _scheme='https'))
    token = client.fetch_token(GOOGLE_TOKEN_URL, client_secret=GOOGLE_CLIENT_SECRET, authorization_response=request.url)
    user_info = client.get("https://openidconnect.googleapis.com/v1/userinfo").json()
    provider_id = user_info.get("sub")
    # Create a new user in the database if it doesn't exist
    user = db.session.get(User, provider_id)
    if not user:
        # Create a Stripe customer
        stripe_customer = stripe.Customer.create(
            email=user_info.get("email"),
            name=user_info.get("name"),
            description="Customer for {}".format(user_info.get("email")),
        )
        user = User(
            provider_id=provider_id, 
            email=user_info.get("email"), 
            name=user_info.get("name"), 
            provider_name='google',  # Set the provider as 'google'
            profile_pic=user_info.get("picture", None),  # Use the 'picture' field from Google, if available
            stripe_customer_id=stripe_customer.id  # Initialize as None; update when integrating with Stripe
        )
        db.session.add(user)
        db.session.commit()
    session["provider_id"] = provider_id
    return redirect(url_for("protected"))


@app.route("/protected")
def protected():
    provider_id = session.get("provider_id")
    if provider_id:
        user = db.session.get(User, provider_id)
        return f"Welcome, {user.name}!"
    return "Not logged in", 401


class User(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=True)
    profile_pic = db.Column(db.String(255), nullable=True)  # URL to the profile picture
    provider = db.Column(db.String(50), nullable=False)  # 'google', 'apple', 'microsoft'
    stripe_customer_id = db.Column(db.String(255), nullable=True)  # Stripe customer ID

    def __repr__(self):
        return f'<User {self.email}>'


if __name__ == "__main__":
    app.run(debug=True)
