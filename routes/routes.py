from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort, current_app
from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session
from models import db, User, Subscription, MobileNumber, History, UserPreference, AssistantPreference  # Import models
from utils.utility import fetch_data
import stripe

stripe.api_key = current_app.config['MICROSOFT_CLIENT_ID']

def configure_routes(app):

    @app.route('/', methods=['GET', 'POST'])
    def index_page():
        return render_template('index.html')

    @app.route('/terms')
    def terms_page():
        return render_template('terms.html')

    @app.route('/privacy')
    def privacy_page():
        return render_template('privacy.html')

    @app.route('/about')
    def about_page():
        return render_template('about.html')

    @app.route('/faq')
    def faq_page():
        return render_template('faq.html')
      
    @app.route('/contact', methods=['POST'])
    def contact_page():
        return render_template('contact.html')

    @app.route('/subscribe', methods=['POST'])
    def subscribe_page():
        return render_template('subscribe.html')
      
    @app.route('/account', methods=['POST'])
    def account_page():
        return render_template('account.html')

    @app.route('/cancel', methods=['POST'])
    def cancel_page():
        return render_template('cancel.html')

    @app.route('/dashboard')
    def dashboard_page():
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return render_template('dashboard.html')

    @app.route("/api/apple/authorize")
    def authorize_apple():
        # Apple-specific OAuth configuration and redirect
        pass

    @app.route("/api/apple/callback")
    def apple_callback():
        # Apple-specific OAuth configuration and redirect
        pass

    @app.route("/api/microsoft/authorize")
    def microsoft_authorize():
        current_app.logger.info('Info: API Call to /api/microsoft/authorize')
        client = OAuth2Session(current_app.config['MICROSOFT_CLIENT_ID'], scope=["openid", "profile", "email"], redirect_uri=url_for("microsoft_callback", _external=True, _scheme='https'))
        uri, state = client.authorization_url(current_app.config['MICROSOFT_AUTHORIZATION_URL'])
        return redirect(uri)

    @app.route("/api/microsoft/callback")
    def microsoft_callback():
        current_app.logger.info('Info: API Call to /api/microsoft/callback')
        client = OAuth2Session(current_app.config['MICROSOFT_CLIENT_ID'], scope=["openid", "profile", "email"], redirect_uri=url_for("microsoft_callback", _external=True, _scheme='https'))
        token = client.fetch_token(current_app.config['MICROSOFT_TOKEN_URL'], client_secret=current_app.config['MICROSOFT_CLIENT_SECRET'], authorization_response=request.url)
        user_info = client.get("https://graph.microsoft.com/oidc/userinfo").json()
        current_app.logger.info('Info: Data Received from Microsoft API Call to /api/microsoft/callback: '+ str(user_info))
        provider_id = user_info.get("sub")
        # Create a new user in the database if it doesn't exist
        user_name = user_info.get("name")
        if not user_name:
            user_name = user_info.get("givenname") + " " + user_info.get("familyname")
        user = User.query.filter_by(provider_id=provider_id).first()
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
        return redirect(url_for("dashboard_page"))

    @app.route("/api/google/authorize")
    def google_authorize():
        current_app.logger.info('Info: API Call to /api/google/authorize')
        client = OAuth2Session(current_app.config['GOOGLE_CLIENT_ID'], scope=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"], redirect_uri=url_for("google_callback", _external=True, _scheme='https'))
        uri, state = client.authorization_url(current_app.config['GOOGLE_AUTHORIZATION_URL'])
        return redirect(uri)

    @app.route("/api/google/callback")
    def google_callback():
        current_app.logger.info('Info: API Call to /api/google/callback')
        client = OAuth2Session(current_app.config['GOOGLE_CLIENT_ID'], scope=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"], redirect_uri=url_for("google_callback", _external=True, _scheme='https'))
        token = client.fetch_token(current_app.config['GOOGLE_TOKEN_URL'], client_secret=current_app.config['GOOGLE_CLIENT_SECRET'], authorization_response=request.url)
        user_info = client.get("https://openidconnect.googleapis.com/v1/userinfo").json()
        provider_id = user_info.get("sub")
        # Create a new user in the database if it doesn't exist
        user = User.query.filter_by(provider_id=provider_id).first()
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
        return redirect(url_for("dashboard_page"))

    @app.route('/api/sms/callback', methods=['POST'])
    def twillio_callback():
        """Replies to SMS messages using data from a POST request.

        Extracts the user's message and phone number from the request,
        validates the user, gets and formats relevant information,
        and uses OpenAI's API to generate a reply. The reply is sent
        back to the user via SMS.

        Returns:
            A tuple containing a string response and an HTTP status code.
        """
        try:
            # Create an instance of RequestValidator
            validator = RequestValidator(TWILIO_AUTH_TOKEN)

            # Retrieve the full URL of the incoming request
            url = request.url

            # Get the POST data as a dictionary
            post_vars = request.form.to_dict()

            # Retrieve the X-Twilio-Signature header from the request
            signature = request.headers.get('X-Twilio-Signature', '')

            # Validate the request
            if not validator.validate(url, post_vars, signature):
                # If invalid, reject the request
                abort(403)

            from_number = post_vars['From']
            to_number = post_vars['To']
            message_body = post_vars['Body']
            message_sid = post_vars.get('MessageSid', 'No SID')
            
            # Validate the user and get the corresponding assistant
            user, assistant = validate_user_and_get_assistant(from_number)

            # Gather relevant info based on the user's message
            gathered_info, history = gather_info(message, user)

            # Build a list of messages for the conversation
            messages = build_messages(gathered_info, history, user, assistant, message)

            # Use OpenAI's API to generate a reply
            reply = generate_reply(messages, user)

            # Send the reply to the user
            send_reply(reply, from_number)

            return 'OK', 200
        except Exception as e:
            print(f"Error: {e}")
            return 'Internal Server Error', 500
