from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort, current_app
from models import db, User, Subscription, MobileNumber, History, UserPreference, AssistantPreference 
from twilio.request_validator import RequestValidator
from twilio.rest import Client
from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session
from utils.utility import fetch_data, check_user_subscription, generate_menu, get_products, handle_stripe_operations, get_location, get_country_code, clean_phone_number, validate_incomming_message, save_sms_history, load_sms_history, build_system_prompt, process_questions_answers, build_and_send_messages, send_reply, build_and_send_messages_openai
import stripe
import aiohttp
import asyncio
import openai
from datetime import datetime

def configure_routes(app):

    @app.after_request
    def add_header(response):
        # Ensure the endpoint is not None before checking its value
        if request.endpoint and 'static' not in request.endpoint:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response
    
    @app.route('/', methods=['GET', 'POST'])
    def index_page():
        if session.get('user_provider_id'):
            member = check_user_subscription(session.get('user_provider_id'))
            is_user = member['is_user']
        else:
            member = check_user_subscription(None)
            is_user = False
        current_app.logger.info('Info: Index Page - Member Object: ' + str(member))
        menu = generate_menu(member)
        return render_template('index.html', menu=menu, is_user=is_user)

    @app.route('/terms')
    def terms_page():
        if session.get('user_provider_id'):
            member = check_user_subscription(session.get('user_provider_id'))
        else:
            member = check_user_subscription(None)
        current_app.logger.info('Info: Terms Page - Member Object: ' + str(member))
        menu = generate_menu(member)
        return render_template('terms.html', menu=menu)

    @app.route('/privacy')
    def privacy_page():
        if session.get('user_provider_id'):
            member = check_user_subscription(session.get('user_provider_id'))
        else:
            member = check_user_subscription(None)
        current_app.logger.info('Info: Privacy Page - Member Object: ' + str(member))
        menu = generate_menu(member)
        return render_template('privacy.html', menu=menu)

    @app.route('/about')
    def about_page():
        if session.get('user_provider_id'):
            member = check_user_subscription(session.get('user_provider_id'))
        else:
            member = check_user_subscription(None)
        current_app.logger.info('Info: About Page - Member Object: ' + str(member))
        menu = generate_menu(member)
        return render_template('about.html', menu=menu)

    @app.route('/faq')
    def faq_page():
        if session.get('user_provider_id'):
            member = check_user_subscription(session.get('user_provider_id'))
        else:
            member = check_user_subscription(None)
        current_app.logger.info('Info: Faq Page - Member Object: ' + str(member))
        menu = generate_menu(member)
        return render_template('faq.html', menu=menu)
      
    @app.route('/contact', methods=['GET', 'POST'])
    def contact_page():
        if session.get('user_provider_id'):
            member = check_user_subscription(session.get('user_provider_id'))
        else:
            member = check_user_subscription(None)
        current_app.logger.info('Info: Contact Page - Member Object: ' + str(member))
        menu = generate_menu(member)
        return render_template('contact.html', menu=menu)

    @app.route('/subscribe', methods=['GET', 'POST'])
    def subscribe_page():
        if session.get('user_provider_id'):
            member = check_user_subscription(session.get('user_provider_id'))
        else:
            member = check_user_subscription(None)
        current_app.logger.info('Info: Subscribe Page - Member Object: ' + str(member))
        menu = generate_menu(member)
        if not member['is_user']:
            return redirect(url_for('index_page'))
        elif not member['is_subscribed']:
            error_message = None
            if request.method == 'POST':
                current_app.logger.info('Received POST request with following form data:')
                for key in request.form:
                    current_app.logger.info(f'{key}: {request.form[key]}')
                    # Validate form data
                    required_fields = [
                        'subscriptionOption', 'assistant-name', 'assistant-origin', 'assistant-gender',
                        'assistant-personality', 'assistant-response-style', 'assistant-demeanor',
                        'assistant-attitude', 'user-name', 'user-location', 'user-mobile', 'user-language',
                        'user-title', 'user-measurement', 'user-description', 'card-name', 'billing-address',
                        'billing-country', 'billing-state', 'billing-zip', 'stripeToken'
                    ]
                    
                    error_message = 'Please complete all required fields.'
                    if all(field in request.form for field in required_fields):
                        user = User.query.filter_by(provider_id=session.get('user_provider_id')).first()
                        if user:
                            success, error_message, subscription_id = handle_stripe_operations(user, request.form)
                            if success:
                                location_dict = get_location(request.form['user-location'])
                                if location_dict['location_text'] != 'null':
                                    location_user = location_dict['location_text']
                                    location_country = location_dict['country_code']
                                else:
                                    location_user = request.form['user-location']
                                    location_country = request.form['billing-country']
                                
                                new_assistant_preference = AssistantPreference(
                                    user_id=user.id,
                                    subscription_id=subscription_id,
                                    assistant_name=request.form['assistant-name'],
                                    assistant_origin=request.form['assistant-origin'],
                                    assistant_gender=request.form['assistant-gender'],
                                    assistant_personality=request.form['assistant-personality'],
                                    assistant_response_style=request.form['assistant-response-style'],
                                    assistant_demeanor=request.form['assistant-demeanor'],
                                    assistant_attitude=request.form['assistant-attitude']
                                )

                                db.session.add(new_assistant_preference)
                                db.session.commit() 

                                new_user_preference = UserPreference(
                                    user_id=user.id,
                                    subscription_id=subscription_id,
                                    user_name=request.form['user-name'],
                                    user_title=request.form['user-title'],
                                    user_measurement=request.form['user-measurement'],
                                    user_bio=request.form.get('user-description', ''),
                                    user_language=request.form['user-language'],
                                    user_location_full=location_user, 
                                    user_location_country=location_country
                                )

                                db.session.add(new_user_preference)
                                db.session.commit()
                                
                                clean_number = clean_phone_number(request.form['user-mobile'])
                                ctry_code = 1

                                new_mobile_number = MobileNumber(
                                    user_id=user.id,
                                    subscription_id=subscription_id,
                                    country_code=ctry_code,
                                    mobile_number=int(clean_number)
                                )
    
                                db.session.add(new_mobile_number)
                                db.session.commit()

                                return redirect(url_for('dashboard_page'))
                    else:
                        current_app.logger.error(error_message)
                        
            product_data = get_products()
            current_app.logger.info('Info: Subscribe Page - Products Object: ' + str(product_data))
            return render_template('subscribe.html', menu=menu, products=product_data, form_data=request.form, error=error_message)

    
    @app.route('/account', methods=['GET', 'POST'])
    def account_page():
        if session.get('user_provider_id'):
            member = check_user_subscription(session.get('user_provider_id'))
        else:
            member = check_user_subscription(None)
        current_app.logger.info('Info: Account Page - Member Object: ' + str(member))
        menu = generate_menu(member)
        if not member['is_user']:
            return redirect(url_for('index_page'))
        elif not member['is_subscribed']:
            return redirect(url_for('subscribe_page'))
        elif member['is_subscribed']:
            user = User.query.filter_by(provider_id=session.get('user_provider_id')).first()
            subscription = Subscription.query.filter_by(user_id=user.id, enabled=True).first()
            try:
                # Fetch customer subscriptions
                subscriptions = stripe.Subscription.list(customer=user.stripe_customer_id)
        
                # Fetch the plan details from Stripe
                stripe_plan = stripe.Price.retrieve(subscription.stripe_plan_id)
                stripe_product = stripe.Product.retrieve(stripe_plan.product)
                
                # Format the dates
                start_date = datetime.strptime(subscription.current_period_start, '%Y-%m-%d %H:%M:%S').strftime('%A, %B %d, %Y')
                end_date = datetime.strptime(subscription.current_period_end, '%Y-%m-%d %H:%M:%S').strftime('%A, %B %d, %Y')
            
                # Determine the interval
                interval = 'Monthly' if stripe_plan.recurring['interval'] == 'month' else 'Yearly'

                subscription_details = {
                    'name': stripe_product.name,
                    'price': f"${stripe_plan.unit_amount / 100:.2f} {stripe_plan.currency.upper()}",
                    'interval': interval,
                    'current_period_start': start_date,
                    'current_period_end': end_date,
                    'status': subscription.status.capitalize()
                }

                # Find the subscription with the specified price ID
                subscription_id = None
                for sub in subscriptions.auto_paging_iter():
                    for item in sub['items']['data']:
                        if item['price']['id'] == subscription.stripe_plan_id:
                            subscription_id = sub['id']
                            break
                    if subscription_id:
                        break
        
                if not subscription_id:
                    return jsonify({'error': 'No subscription found for the specified price ID'}), 404

                # Fetch invoices for the subscription
                invoices = stripe.Invoice.list(
                    customer=user.stripe_customer_id,
                    subscription=subscription_id,
                    limit=24  # Adjust the limit as needed
                )

                # Extract relevant data from each invoice
                invoice_data = []
                for invoice in invoices.auto_paging_iter():
                    invoice_data.append({
                        'number': invoice.number,
                        'type': 'Subscription',  # Assuming all invoices are for subscriptions
                        'date': datetime.fromtimestamp(invoice.created).strftime('%Y-%m-%d %H:%M:%S'),
                        'amount': invoice.amount_due / 100,  # Convert cents to dollars
                        'status': invoice.status,
                        'receipt_url': invoice.hosted_invoice_url  # URL for the printable receipt
                    })

                return render_template('account.html', menu=menu, invoices=invoice_data, subscription_details=subscription_details)
        
            except Exception as e:
                return jsonify({'error': str(e)}), 500


    @app.route('/cancel', methods=['GET', 'POST'])
    def cancel_page():
        if session.get('user_provider_id'):
            member = check_user_subscription(session.get('user_provider_id'))
        else:
            member = check_user_subscription(None)
        current_app.logger.info('Info: Cancel Page - Member Object: ' + str(member))
        menu = generate_menu(member)
        if not member['is_user']:
            return redirect(url_for('index_page'))
        elif not member['is_subscribed']:
            return redirect(url_for('subscribe_page'))
        elif member['is_subscribed']:
            return render_template('cancel.html', menu=menu)

    @app.route('/dashboard', methods=['GET', 'POST'])
    def dashboard_page():
        if session.get('user_provider_id'):
            member = check_user_subscription(session.get('user_provider_id'))
        else:
            member = check_user_subscription(None)
        current_app.logger.info('Info: Dashboard Page - Member Object: ' + str(member))
        menu = generate_menu(member)
        if not member['is_user']:
            return redirect(url_for('index_page'))
        elif not member['is_subscribed']:
            return redirect(url_for('subscribe_page'))
        elif member['is_subscribed'] and not member['has_billing_error']:
            return render_template('dashboard.html', menu=menu)
        elif member['is_subscribed'] and member['has_billing_error']:
            return redirect(url_for('account_page'))

    @app.route('/logout')
    def logout():
        # Clear all data from the session
        session.clear()
     
        # Redirect to login page
        response = redirect(url_for('index_page'))

        # Delete cookies
        for key in request.cookies:
            response.delete_cookie(key)

        # Redirect to the homepage
        return response
    
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
        session["user_provider_id"] = provider_id
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
        session["user_provider_id"] = provider_id
        return redirect(url_for("dashboard_page"))



    @app.route('/api/sms/callback', methods=['POST'])
    def twilio_callback():
        try:
            # Create an instance of RequestValidator
            validator = RequestValidator(app.config['TWILIO_AUTH_TOKEN'])
     
            # Create an instance of Client
            client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])

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

            # Extract relevant Twilio message fields
            from_number = post_vars['From']
            to_number = post_vars['To']
            message_body = post_vars['Body']
            message_sid = post_vars.get('MessageSid', 'No SID')
            account_sid = post_vars.get('AccountSid', 'No Account SID')
            sms_status = post_vars.get('SmsStatus', 'No Status')
            num_media = post_vars.get('NumMedia', '0')
            twilio_phone_number = client.incoming_phone_numbers.list(phone_number=to_number)
        
            if twilio_phone_number:
                twilio_phone_number_sid = twilio_phone_number[0].sid
            else:
                twilio_phone_number_sid = None
        
            if not twilio_phone_number_sid:
                return 'Unauthorized', 403

            # Log the incoming request details
            current_app.logger.info(f'Incoming SMS: From={from_number}, To={to_number}, Body={message_body}, SID={message_sid}, Account SID={account_sid}, Phone Number SID: {twilio_phone_number_sid}, Status={sms_status}, Media={num_media}')

            # Validate the user and get the corresponding assistant
            user_id, subscription_id = validate_incomming_message(from_number, twilio_phone_number_sid)

            # Log the user validation details
            current_app.logger.info(f'Validated User: User ID={user_id}, Subscription ID={subscription_id}, From Number={from_number}')

            save_sms_history(user_id, subscription_id, message_sid, 'incoming', from_number, to_number, message_body, sms_status)

            user_preferences = UserPreference.query.filter_by(user_id=user_id, subscription_id=subscription_id).first()

            assistant_preferences = AssistantPreference.query.filter_by(user_id=user_id, subscription_id=subscription_id).first()

            message_answers = None
            # Run the asynchronous process_questions_answers function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            message_answers = loop.run_until_complete(process_questions_answers(message_body, user_preferences.user_location_full, user_preferences.user_location_country))

            prompt = build_system_prompt(user_preferences, assistant_preferences, message_answers)

            current_app.logger.info(f'Assistant System Prompt: {prompt}')       

            chat_history = load_sms_history(user_id, subscription_id, order='desc')

            current_app.logger.debug(f"twilio_callback() Position 1")

            #outgoing_message = build_and_send_messages(prompt, chat_history)     

            outgoing_message = build_and_send_messages_openai(prompt, chat_history)  

            current_app.logger.info(f'Assistant Response: {outgoing_message}')

            send_reply(user_id, subscription_id, outgoing_message, from_number, to_number, client)

            current_app.logger.debug(f"twilio_callback() Position 2")
        
            if not user_id or not subscription_id:
                return 'Unauthorized', 403

            return 'OK', 200
        except Exception as e:
            current_app.logger.error(f"Error: {e}")
            return 'Internal Server Error', 500
