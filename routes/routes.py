from flask import Flask, render_template, request, redirect, url_for, session, jsonify

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

    @app.route("api/apple/callback")
    def apple_callback():
        # Apple-specific OAuth configuration and redirect
        pass

    @app.route("/api/microsoft/authorize")
    def authorize_microsoft():
        client = OAuth2Session(MICROSOFT_CLIENT_ID, scope=["openid", "profile", "email"], redirect_uri=url_for("microsoft_callback", _external=True, _scheme='https'))
        uri, state = client.authorization_url(MICROSOFT_AUTHORIZATION_URL)
        return redirect(uri)

    @app.route("/api/microsoft/callback")
    def microsoft_callback():
        client = OAuth2Session(MICROSOFT_CLIENT_ID, scope=["openid", "profile", "email"], redirect_uri=url_for("microsoft_callback", _external=True, _scheme='https'))
        token = client.fetch_token(MICROSOFT_TOKEN_URL, client_secret=MICROSOFT_CLIENT_SECRET, authorization_response=request.url)
        user_info = client.get("https://graph.microsoft.com/oidc/userinfo").json()
        user_id = user_info.get("sub")
        print(user_info)
        # Create a new user in the database if it doesn't exist
        user_name = user_info.get("name")
        if not user_name:
            user_name = user_info.get("givenname") + " " + user_info.get("familyname")
        user = db.session.get(User, user_id)
        if not user:
            # Create a Stripe customer
            stripe_customer = stripe.Customer.create(
                email=user_info.get("email"),
                name=user_name,
                description="Customer for {}".format(user_info.get("email")),
            )
            user = User(
                id=user_id,
                email=user_info.get("email"),
                name=user_name,
                provider='microsoft',  # Set the provider as 'microsoft'
                profile_pic=user_info.get("picture", None),  # Use the 'picture' field from Microsoft, if available
                stripe_customer_id=stripe_customer.id  # Initialize as None; update when integrating with Stripe
            )
            db.session.add(user)
            db.session.commit()
        session["user_id"] = user_id
        return redirect(url_for("protected"))

    @app.route("/api/google/authorize")
    def authorize_google():
        client = OAuth2Session(GOOGLE_CLIENT_ID, scope=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"], redirect_uri=url_for("callback", _external=True, _scheme='https'))
        uri, state = client.authorization_url(GOOGLE_AUTHORIZATION_URL)
        return redirect(uri)

    @app.route("/api/google/callback")
    def callback():
        client = OAuth2Session(GOOGLE_CLIENT_ID, scope=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"], redirect_uri=url_for("callback", _external=True, _scheme='https'))
        token = client.fetch_token(GOOGLE_TOKEN_URL, client_secret=GOOGLE_CLIENT_SECRET, authorization_response=request.url)
        user_info = client.get("https://openidconnect.googleapis.com/v1/userinfo").json()
        user_id = user_info.get("sub")
        # Create a new user in the database if it doesn't exist
        user = db.session.get(User, user_id)
        if not user:
            # Create a Stripe customer
            stripe_customer = stripe.Customer.create(
                email=user_info.get("email"),
                name=user_info.get("name"),
                description="Customer for {}".format(user_info.get("email")),
            )
            user = User(
                id=user_id, 
                email=user_info.get("email"), 
                name=user_info.get("name"), 
                provider='google',  # Set the provider as 'google'
                profile_pic=user_info.get("picture", None),  # Use the 'picture' field from Google, if available
                stripe_customer_id=stripe_customer.id  # Initialize as None; update when integrating with Stripe
            )
            db.session.add(user)
            db.session.commit()
        session["user_id"] = user_id
        return redirect(url_for("protected"))

    @app.route('/api/sms/callback', methods=['POST'])
    def sms_reply():
        """Replies to SMS messages using data from a POST request.

        Extracts the user's message and phone number from the request,
        validates the user, gets and formats relevant information,
        and uses OpenAI's API to generate a reply. The reply is sent
        back to the user via SMS.

        Returns:
            A tuple containing a string response and an HTTP status code.
        """
        try:
            # Extract and clean data from the request
            from_number, message = get_data_from_request(request)

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
