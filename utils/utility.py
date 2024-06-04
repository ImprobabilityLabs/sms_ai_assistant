import requests
import json
from groq import Groq
import sys
import re
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort, current_app
from models import db, User, Subscription, MobileNumber, History, UserPreference, AssistantPreference 
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from flask_sqlalchemy import SQLAlchemy
from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session
import requests
import stripe
import os
from datetime import datetime
import phonenumbers
from phonenumbers.phonenumberutil import region_code_for_number
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import aiohttp
import asyncio
import regex
from openai import OpenAI
import secrets
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def remove_keys(data, keys_to_remove):
    """ Recursively remove specified keys from a dictionary. """
    if isinstance(data, dict):
        return {key: remove_keys(value, keys_to_remove) for key, value in data.items() if key not in keys_to_remove}
    elif isinstance(data, list):
        return [remove_keys(item, keys_to_remove) for item in data]
    else:
        return data

async def fetch_data(question, location=None):
    """Fetch data from the DataForSEO API for the specified question."""
    url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
    
    current_app.logger.debug(f"fetch_data() Question Input: {question}")

    # Set location code based on input
    location_code = 2840  # Default to US location code
    if location == 'US':
        location_code = 2840
    elif location == 'CA':
        location_code = 2124
    
    # Prepare payload
    payload = json.dumps([{
        "keyword": question,
        "location_code": location_code,
        "language_code": "en",
        "device": "desktop",
        "os": "windows",
        "depth": 1
    }])
    
    headers = {
        'Authorization': f"Basic {current_app.config['SEO_FOR_DATA_KEY']}",
        'Content-Type': 'application/json'
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, data=payload, timeout=10) as response:
                current_app.logger.debug(f"fetch_data() Position 1 - Response Status: {response.status}")
                response.raise_for_status()  # Raise an exception for bad responses
                response_text = await response.text()
                current_app.logger.debug(f"fetch_data() Position 2 - Response Text: {response_text}")
                data = await response.json()
                current_app.logger.debug(f"fetch_data() Position 3 - JSON Data: {data}")
                
                # Check if the response contains the expected data
                if 'tasks' in data and len(data['tasks']) > 0 and 'result' in data['tasks'][0]:
                    return data['tasks'][0]['result']
                else:
                    current_app.logger.warning("fetch_data() - No result found in the response")
                    return None  # Or handle the case where the result is not found

        except aiohttp.ClientError as e:
            current_app.logger.error(f"Request failed: {e}")
            current_app.logger.error("fetch_data() Request Exception Error")
            return None

        except json.JSONDecodeError:
            current_app.logger.error("fetch_data() JSONDecodeError - Failed to decode JSON response")
            return None

        except KeyError:
            current_app.logger.error("fetch_data() KeyError - Unexpected response structure")
            return None


def clean_data(data):
    """ Remove unnecessary keys from the data. """
    keys_to_remove = {'xpath', 'image_url', 'url', 'images', 'cache_url', 'is_image', 'is_video', 'type',
                      'rank_group', 'rank_absolute', 'position', 'rectangle', 'reviews_count', 'rating',
                      'place_id', 'feature', 'cid', 'data_attrid', 'domain', 'faq', 'extended_people_also_search',
                      'about_this_result', 'timestamp', 'related_result', 'se_domain', 'location_code',
                      'language_code', 'check_url', 'datetime', 'se_results_count', 'items_count', 'related_search_url',
                      'breadcrumb', 'is_malicious', 'is_web_story', 'amp_version', 'card_id', 'logo_url',
                      'is_featured_snippet', 'pre_snippet', 'extended_snippet', 'price', 'links'}
    cleaned_data = remove_keys(data, keys_to_remove)
    return json.dumps(cleaned_data, indent=2)


async def answer_question(question, data):
    current_app.logger.debug(f"answer_question - Question Input: {question}")
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {current_app.config['GROQ_KEY']}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {
                    "role": "system",
                    "content": f"Extract the answer to '{question}', and output it in a paragraph with any additional relevant information. Try and convert any company name to their stock symbols in the outputted questions."
                },
                {
                    "role": "user",
                    "content": data
                }
            ],
            "temperature": 1,
            "max_tokens": 256,
            "top_p": 1,
            "stream": False,
            "stop": None
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=10) as response:
                response.raise_for_status()
                response_json = await response.json()
                current_app.logger.debug(f"answer_question() Position 1 - Response JSON: {response_json}")
                return response_json['choices'][0]['message']['content']
    except Exception as e:
        current_app.logger.error(f"An error occurred: {e}")
        current_app.logger.error("answer_question() Exception Error")
        return None
        
def extract_questions(message_text):
    current_app.logger.debug(f"extract_questions - Message Text: {message_text}")
    try:
        # Ensure message_text is a string
        if not isinstance(message_text, str):
            raise ValueError("message_text must be a string")

        client = Groq()
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "Extract questions from the text. Reframe each question to make it standalone and understandable without requiring additional context. Output each question on a separate line with a question mark. Only output Questions. Ignore questions related to personal or specific context that cannot be understood or answered without additional private knowledge. Do not include Notes or extra information. If no questions are found reply without a question mark."
                },
                {
                    "role": "user",
                    "content": json.dumps(message_text)
                }
            ],
            temperature=1,
            max_tokens=386,
            top_p=1,
            stream=False,
            stop=None,
        )

        print(f"Tokens: {completion.usage}")

        lines = completion.choices[0].message.content.split('\n')
        current_app.logger.debug(f"extract_questions - Dirty Questions: {lines}")

        # Filter lines containing the question mark and clean them
        filtered_questions = [
            re.sub(r"[^\w\s?.-]", "", line).strip() for line in lines if '?' in line
        ]
        current_app.logger.debug(f"extract_questions - Filtered Questions: {filtered_questions}")
        return filtered_questions

    except Exception as e:
        current_app.logger.error(f"An error occurred: {e}")
        current_app.logger.error("extract_questions() Exception Error")
        return []


def check_user_subscription(provider_id):
    # Initialize the result dictionary
    result = {
        "is_user": False,
        "is_subscribed": False,
        "has_billing_error": False
    }
    
    # Query the user based on provider_id
    user = User.query.filter_by(provider_id=provider_id).first()
    
    # Check if the user exists
    if user:
        result['is_user'] = True
        
        # Query the subscription based on user id and check if it is enabled
        subscription = Subscription.query.filter_by(user_id=user.id, enabled=True).first()
        
        if subscription:
            result['is_subscribed'] = True
            
            # Check if there is a billing error
            if subscription.billing_error:
                result['has_billing_error'] = True
                
    return result

def generate_menu(member):
    if not member['is_user']: 
        menu = [
            {"name": "Home", "url": "/"},
            {"name": "About", "url": "/about"},
            {"name": "FAQ", "url": "/faq"},
            {"name": "Contact", "url": "/contact"},
        ]
    elif member['is_user'] and not member['is_subscribed']:
        menu = [
            {"name": "Home", "url": "/"},
            {"name": "Subscribe", "url": "/subscribe"},
            {"name": "Contact", "url": "/contact"},
            {"name": "Logout", "url": "/logout"},
        ]
    elif member['is_user'] and member['is_subscribed'] and not member['has_billing_error']:
        menu = [
            {"name": "Home", "url": "/"},
            {"name": "Dashboard", "url": "/dashboard"},
            {"name": "Account", "url": "/account"},
            {"name": "Logout", "url": "/logout"},
        ]
    elif member['is_user'] and member['is_subscribed'] and member['has_billing_error']:
        menu = [
            {"name": "Home", "url": "/"},
            {"name": "Account", "url": "/account"},
            {"name": "Contact", "url": "/contact"},
            {"name": "Logout", "url": "/logout"},
        ]
    return menu

def get_products():
    products = stripe.Product.list(limit=10)  # Adjust limit as necessary

    product_data = []

    for product in products.auto_paging_iter():
        # Retrieve prices associated with the product
        prices = stripe.Price.list(product=product.id, type='recurring')

        for price in prices.data:
            # Access price fields
            price_id = price.id
            amount = price.unit_amount / 100
            currency = price.currency.upper()
            interval = price.recurring.interval

            # Retrieve product details including description
            description = product.description or ""

            # Access metadata
            country = product.metadata.get('country', '')
            tax = float(product.metadata.get('tax', 0.0))
            tax_name = product.metadata.get('tax_name', '')

            # Extract feature names from the features and marketing_features
            features = [feature['name'] for feature in product.get('features', [])]

            # Handle the image URL
            images = product.images
            image_url = images[0] if images else 'https://example.com/default-image.jpg'  # Default image if none available

            # Append to product data
            product_data.append({
                'product_id': product.id,
                'price_id': price_id,
                'amount': f"{amount:.2f}",
                'currency': currency,
                'interval': interval,
                'description': description,
                'country': country,
                'features': features,
                'image_url': image_url,
                'product_name': product.name
            })

    return product_data


def update_customer_billing_info(user, form_data):
    try:
        # Retrieve the existing customer
        customer = stripe.Customer.retrieve(user.stripe_customer_id)
        
        # Update customer details
        customer.name = sanitize_string(form_data['card-name'], 30),
        customer.email = sanitize_string(user.email, 255),
        customer.address = {
            'line1': sanitize_string(form_data['billing-address'], 255),
            'country': sanitize_string(form_data['billing-country'], 2),
            'state': sanitize_string(form_data['billing-state'], 128),
            'postal_code': sanitize_string(form_data['billing-zip'], 20),
        }
        
        # Save the updated customer information
        customer.save()
        
        # Log the successful update
        current_app.logger.info("Updated customer billing information for user ID %s.", user.id)
        
        return True
    except Exception as e:
        # Log the error
        current_app.logger.error("Failed to update customer billing information for user ID %s. Error: %s", user.id, str(e))
        
        return False


def create_and_attach_payment_method(user, form_data):
    try:
        # Create the payment method
        payment_method = stripe.PaymentMethod.create(
            type="card",
            card={"token": form_data['stripeToken']},
            billing_details={
                'name': sanitize_string(form_data['card-name'], 30),
                'email': sanitize_string(user.email, 255),
                'address': {
                    'line1': sanitize_string(form_data['billing-address'], 255),
                    'country': sanitize_string(form_data['billing-country'], 2),
                    'state': sanitize_string(form_data['billing-state'], 128),
                    'postal_code': sanitize_string(form_data['billing-zip'], 20),
                }
            }
        )
        current_app.logger.info("Created new payment method for user ID %s.", user.id)

        # Attach the payment method to the customer
        stripe.PaymentMethod.attach(
            payment_method.id,
            customer=user.stripe_customer_id,
        )
        current_app.logger.info("Attached payment method to customer for user ID %s.", user.id)

        # Set the new payment method as the default
        stripe.Customer.modify(
            user.stripe_customer_id,
            invoice_settings={
                'default_payment_method': payment_method.id,
            },
        )
        current_app.logger.info("Set new payment method as default for user ID %s.", user.id)

        return True, None
        
    except stripe.error.CardError as e:
        # Handle card errors like declined, expired, etc.
        error_body = e.json_body
        card_err = error_body.get('error', {})
        error_message = card_err.get('message', 'Problem with card.')
        current_app.logger.warning("Card error for user ID %s. Error: %s", user.id, error_message)
        return False, error_message

    except stripe.error.StripeError as e:
        # Handle other Stripe errors
        current_app.logger.error("Stripe error for user ID %s. Error: %s", user.id, str(e))
        return False, str(e)

    except Exception as e:
        # Handle any other errors
        current_app.logger.error("Failed to create or attach payment method for user ID %s. Error: %s", user.id, str(e))
        return False, str(e)



def handle_stripe_operations(user, form_data, referrer, url_base):
    try:
        current_app.logger.info("Starting Stripe operations for user: %s", user.id)

        if not user.stripe_customer_id:
            raise ValueError("Stripe customer ID not found for user.")

        current_app.logger.info("Retrieved Stripe customer ID: %s", user.stripe_customer_id)

        update_customer = update_customer_billing_info(user, form_data)

        if not update_customer:
            return False, 'Error saving Stripe Customer', -1

        # Conditionally apply tax rates based on the billing country
        tax_rate_ids = get_tax_rate_ids(form_data['billing-country'])
        current_app.logger.info("Retrieved tax rate IDs: %s", tax_rate_ids)

        payment_info_update, payment_info_error = create_and_attach_payment_method(user, form_data)	    

        if not payment_info_update:
            return False, payment_info_error, -1
		
        # Create or update the Stripe subscription
        subscription = stripe.Subscription.create(
            customer=user.stripe_customer_id,
            items=[{'price': form_data['subscriptionOption']}],
            default_tax_rates=tax_rate_ids,
            expand=['latest_invoice.payment_intent', 'latest_invoice'],
        )
        current_app.logger.info("Created new subscription.")

        # Check if the payment was successful
        payment_intent = subscription.latest_invoice.payment_intent
        if payment_intent.status != 'succeeded':
            stripe.Subscription.delete(subscription.id)
            raise ValueError("Payment was not successful.")
        current_app.logger.info("Payment was successful.")

        # Extract necessary fields from the subscription
        subscription_id = subscription.id
        current_period_start = datetime.utcfromtimestamp(subscription.current_period_start).strftime('%Y-%m-%d %H:%M:%S')
        current_period_end = datetime.utcfromtimestamp(subscription.current_period_end).strftime('%Y-%m-%d %H:%M:%S')
        status = subscription.status.capitalize()

        stripe_product = stripe.Product.retrieve(id=subscription.plan.product)

        stripe_product_country = stripe_product.metadata.get('country', '')

        # Clean phone number and save it
        clean_number = clean_phone_number(form_data['user-mobile'])
        mobile_number = '+1'+str(clean_number)

        # Get Twilio number and SID (replace with appropriate function)
        twilio_client = Client(current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN'])
        twilio_numr, twilio_sid = search_and_buy_sms_number(mobile_number, twilio_client, str(stripe_product_country), url_base)

        current_app.logger.info("handle_stripe_operations: Creating New subscription record.")
	    
        # Create a new Subscription record in the database
        new_subscription = Subscription(
            user_id=user.id,
            stripe_customer_id=user.stripe_customer_id,
            stripe_plan_id=subscription.plan.id,
            stripe_product_id=subscription.plan.product,
            twillio_number=twilio_numr,
            twillio_number_sid=twilio_sid,
            stripe_subscription_id=subscription.id,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            status=status,
            referrer=referrer
        )

        # Add the new subscription to the database
        db.session.add(new_subscription)
        db.session.commit()
        current_app.logger.info("New subscription record added to the database.")

        subscription_id = new_subscription.id

        current_app.logger.info('Subscription created successfully for user: %s', user.id)
        return True, None, subscription_id

    except stripe.error.StripeError as e:
        current_app.logger.error(f'Stripe error: {e.user_message}')
        return False, e.user_message, -1
    except Exception as e:
        current_app.logger.error(f'Error: {str(e)}')
        return False, str(e), -1
	    

def update_billing_info(user, form_data):
    try:
        if not user.stripe_customer_id:
            # Raise an exception if the Stripe customer ID does not exist
            raise ValueError("Stripe customer ID not found for user.")

        # Retrieve the existing customer and update the billing information
        customer = stripe.Customer.retrieve(user.stripe_customer_id)
        customer.name = sanitize_string(form_data['card-name'], 30),
        customer.email = sanitize_string(user.email, 255),
        customer.address = {
            'line1': sanitize_string(form_data['billing-address'], 255),
            'country': sanitize_string(form_data['billing-country'], 2),
            'state': sanitize_string(form_data['billing-state'], 128),
            'postal_code': sanitize_string(form_data['billing-zip'], 20),
        }
        customer.save()

        # Save the current default payment method
        old_payment_method = customer.invoice_settings.default_payment_method

        # Convert token to PaymentMethod and attach it to the customer
        payment_method = stripe.PaymentMethod.create(
            type="card",
            card={"token": form_data['stripeToken']},
            billing_details={
                'name': sanitize_string(form_data['card-name'], 30),
                'email': sanitize_string(user.email, 255),
                'address': {
                    'line1': sanitize_string(form_data['billing-address'], 255),
                    'country': sanitize_string(form_data['billing-country'], 2),
                    'state': sanitize_string(form_data['billing-state'], 128),
                    'postal_code': sanitize_string(form_data['billing-zip'], 20),
                }
            }
        )

        # Attach the new payment method to the customer
        stripe.PaymentMethod.attach(
            payment_method.id,
            customer=user.stripe_customer_id,
        )

        # Set the new payment method as the default
        stripe.Customer.modify(
            user.stripe_customer_id,
            invoice_settings={
                'default_payment_method': payment_method.id,
            },
        )

        # Conditionally apply tax rates based on the billing country
        tax_rate_ids = get_tax_rate_ids(form_data['billing-country'])

        # Pay any outstanding invoices immediately
        invoices = stripe.Invoice.list(customer=user.stripe_customer_id, status='open')
        for invoice in invoices:
            try:
                stripe.Invoice.pay(invoice.id)
            except stripe.error.StripeError as pay_error:
                current_app.logger.error(f'Error paying invoice {invoice.id}: {pay_error.user_message}')

        # Delete the old payment method if the new one works without issues
        if old_payment_method:
            stripe.PaymentMethod.detach(old_payment_method)

        current_app.logger.info('Billing Information Updated and outstanding invoices paid.')
        return True, None

    except stripe.error.StripeError as e:
        current_app.logger.error(f'Stripe error: {e.user_message}')
        
        # Detach the new payment method if it was successfully created and attached
        try:
            if payment_method and payment_method.customer:
                stripe.PaymentMethod.detach(payment_method.id)
        except Exception as detach_error:
            current_app.logger.error(f'Error detaching new payment method: {detach_error}')
            
        # Set the old payment method as the default if there was one
        if old_payment_method:
            stripe.Customer.modify(
                user.stripe_customer_id,
                invoice_settings={
                    'default_payment_method': old_payment_method,
                },
            )
        return False, e.user_message
    except Exception as e:
        current_app.logger.error(f'Error: {str(e)}')
        return False, str(e)


async def process_questions_answers(text_message, location, location_country='US'):
    try:
        # Trim whitespace from the text message
        text_message = text_message.strip()
        text_loc = f"Users Location for Questions: {location}\n"
        text_message = text_loc + text_message         

        # Check if text_message is empty
        if not text_message:
            current_app.logger.error("Empty text message received.")
            return None

        current_app.logger.debug(f"process_questions_answers() Position 1")
        # Check if questions is a list
        questions = extract_questions(text_message)
        current_app.logger.debug(f"process_questions_answers() Position 2")
        
        answers = []
        current_app.logger.debug(f"process_questions_answers - Questions: {questions}")
        for question in questions:
            current_app.logger.debug(f"process_questions_answers - Question: {question}")
            fetched_answer = await fetch_data(question, location_country)
            current_app.logger.debug(f"process_questions_answers() Position 3")
            
            if fetched_answer is None:
                current_app.logger.warning(f"No answer fetched for question: {question}")
                continue
            
            cleaned_answer = clean_data(fetched_answer)
           
            answer = await answer_question(question, cleaned_answer)
           
            current_app.logger.debug(f"Answer: {answer}")
            answers.append(answer)

        return answers
        
    except Exception as e:
        current_app.logger.error(f"Error in process_questions_answers: {e}")
        return None


def save_user_and_assistant_preferences(user, subscription_id, form_data):
    try:
        # Get location details
        location_dict = get_location(form_data['user-location'])
        if location_dict and location_dict.get('location_text') != 'null':
            location_user = location_dict['location_text']
            location_country = location_dict['country_code']
        else:
            location_user = form_data['user-location']
            location_country = form_data['billing-country']
        
        # Save assistant preferences
        new_assistant_preference = AssistantPreference(
            user_id=user.id,
            subscription_id=subscription_id,
            assistant_name=sanitize_string(form_data['assistant-name'], 64),
            assistant_origin=sanitize_string(form_data['assistant-origin'], 64),
            assistant_gender=sanitize_string(form_data['assistant-gender'], 64),
            assistant_personality=sanitize_string(form_data['assistant-personality'], 64),
            assistant_response_style=sanitize_string(form_data['assistant-response-style'], 64)
        )
        db.session.add(new_assistant_preference)
        
        # Save user preferences
        new_user_preference = UserPreference(
            user_id=user.id,
            subscription_id=subscription_id,
            user_name=sanitize_string(form_data['user-name'], 64),
            user_title=sanitize_string(form_data['user-title'], 64),
            user_measurement=sanitize_string(form_data['user-measurement'], 64),
            user_bio=sanitize_string(form_data.get('user-description', ''), 512),
            user_language=sanitize_string(form_data['user-language'], 64),
            user_location_full=sanitize_string(location_user, 64), 
            user_location_country=sanitize_string(location_country, 3)
        )
        db.session.add(new_user_preference)
        
        # Commit preferences
        db.session.commit()
        
        # Clean phone number and save it
        clean_number = clean_phone_number(form_data['user-mobile'])
        ctry_code = 1  # Assuming country code is 1
        
        new_mobile_number = MobileNumber(
            user_id=user.id,
            subscription_id=subscription_id,
            country_code=ctry_code,
            mobile_number=int(clean_number)
        )
        db.session.add(new_mobile_number)
        
        # Commit mobile number
        db.session.commit()
        
        current_app.logger.info("Saved user and assistant preferences for user ID %s.", user.id)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Failed to save user and assistant preferences for user ID %s. Error: %s", user.id, str(e))
        return False
    
    return True


def get_tax_rate_ids(country_code):
    tax_rate_ids = []
    if country_code == 'CA': 
        tax_rates = stripe.TaxRate.list(active=True)
        current_app.logger.error("get_tax_rate_ids: "+str(tax_rates))
        for tax_rate in tax_rates.data:  
            if tax_rate.country == 'CA':
                tax_rate_ids.append(tax_rate.id)
    return tax_rate_ids


def send_new_subscription_communications(subscription_id):
    # Retrieve subscription, user preferences, and assistant preferences
    subscription = Subscription.query.filter_by(id=subscription_id, enabled=True).first()
    user = User.query.filter_by(id=subscription.user_id).first()
    user_preferences = UserPreference.query.filter_by(user_id=subscription.user_id, subscription_id=subscription.id).first()
    assistant_preferences = AssistantPreference.query.filter_by(user_id=subscription.user_id, subscription_id=subscription.id).first()
    mobile = MobileNumber.query.filter_by(user_id=subscription.user_id, subscription_id=subscription.id).first()

    # Build system prompt for the welcome message
    sys_prompt = build_system_prompt(
        user_preferences,
        assistant_preferences,
        extra_info=None,
        system_message='Create an initial introduction and welcome message for your user in their preffered language.'
    )

    # Generate the welcome message
    welcome_message = build_and_send_messages_openai(sys_prompt, history_records=None)

    # Send the welcome message
    send_reply(
        user_id=subscription.user_id,
        subscription_id=subscription_id,
        reply=welcome_message,
        to_number='+1'+str(mobile.mobile_number),
        from_number=subscription.twillio_number,
        twilio_client=Client(current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN']),
        save_message=True
    )

    # Send new subscription email
    send_new_subscription_email(
        user_name=user.name,
        user_email=user.email,
        user_number='+1'+str(mobile.mobile_number),
        assistant_name=assistant_preferences.assistant_name,
        assistant_number=subscription.twillio_number
    )
	
                
def clean_phone_number(phone_number):
    # Remove all non-numeric characters
    clean_number = re.sub(r'\D', '', phone_number)
    return clean_number

def get_country_code(phone_number):
    # Parse the phone number
    parsed_number = phonenumbers.parse(phone_number, "US")  # Default region as "US" for North America
    # Extract the country code
    country_code = parsed_number.country_code
    return country_code

def get_location(location_txt):
    try:
        client = Groq()
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "Convert the users input into a Location Full Text(City, State or Province, Country) and Country ISO Code( ISO 3166-1 alpha-2). If the location does not match, respond with null.\n\nRespond in a JSON Format with 2 fields (location_text, country_code) and no other text."
                },
                {
                    "role": "user",
                    "content": json.dumps(location_txt, indent=2)
                }
            ],
            temperature=1,
            max_tokens=128,
            top_p=1,
            stream=False,
            stop=None,
        )

        output = completion.choices[0].message.content

        return json.loads(output)

    except Exception as e:
        print(f"Error occurred: {e}")
        return False


def validate_incomming_message(from_number, phone_sid):
    try:
        # Parse the phone number to extract the country code and mobile number
        parsed_number = phonenumbers.parse(from_number)
        country_code = parsed_number.country_code
        mobile_number = parsed_number.national_number

        # Find the subscription using the account SID and from_number
        subscription = Subscription.query.filter_by(
            twillio_number_sid=phone_sid,
            enabled=1,
            billing_error=0
        ).first()

        if not subscription.user_id or not subscription.id or not subscription:
            current_app.logger.error(f"No subscription found for Twilio Number SID: {phone_sid}")
            return None, None

        # Check if the user_id and subscription_id match in the MobileNumber table
        mobile_entry = MobileNumber.query.filter_by(
            user_id=subscription.user_id,
            subscription_id=subscription.id,
            country_code=country_code,
            mobile_number=mobile_number
        ).first()

        if not mobile_entry:
            current_app.logger.error(f"No matching mobile number found for User ID: {subscription.user_id}, Subscription ID: {subscription.id}, From Number: {from_number}")
            return None, None

        user_id = subscription.user_id
        subscription_id = subscription.id

        return user_id, subscription_id
    except Exception as e:
        current_app.logger.error(f"Error in validate_incomming_message: {e}")
        return None, None


def save_sms_history(user_id, subscription_id, message_sid, direction, from_number, to_number, body=None, status=None):
    current_app.logger.debug(f"save_sms_history() called with user_id={user_id}, subscription_id={subscription_id}, message_sid={message_sid}, direction={direction}, from_number={from_number}, to_number={to_number}, body={body}, status={status}")

    # Create a new History instance
    try:
        history_record = History(
            user_id=user_id,
            subscription_id=subscription_id,
            message_sid=message_sid,
            direction=direction,
            from_number=from_number,
            to_number=to_number,
            body=body,
            status=status
        )
        current_app.logger.debug("History record created successfully")

        # Add the record to the session
        db.session.add(history_record)
        current_app.logger.debug("History record added to the session")

        # Commit the session to the database
        db.session.commit()
        current_app.logger.info("History record committed to the database successfully")
        return True
    except Exception as e:
        # Handle any exceptions that occur during commit
        db.session.rollback()
        current_app.logger.error(f"Error saving history record: {e}", exc_info=True)
        return False



def load_sms_history(user_id, subscription_id, order='asc'):
    """
    Load chat history for a specific user and subscription.

    :param user_id: ID of the user
    :param subscription_id: ID of the subscription
    :param order: 'asc' for oldest to newest, 'desc' for newest to oldest
    :return: List of History records
    """
    if order not in ['asc', 'desc']:
        raise ValueError("Order must be 'asc' or 'desc'")

    # Query the History table
    query = History.query.filter_by(user_id=user_id, subscription_id=subscription_id)
    
    # Order by created column
    if order == 'asc':
        query = query.order_by(History.created.asc())
    else:
        query = query.order_by(History.created.desc())

    # Execute the query and return results
    return query.all()

def build_system_prompt(user_preferences, assistant_preferences, extra_info=None, system_message = None):
    """Builds a system prompt.

    Args:
        user_preferences: An instance of UserPreference.
        assistant_preferences: An instance of AssistantPreference.
        extra_info: Additional information to append at the end of the prompt. Can be a string, a list of strings, or None.

    Returns:
        A JSON-safe string containing the system prompt.
    """
    current_time_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    system_prompt = (
        f"You are a virtual SMS assistant named {assistant_preferences.assistant_name}, known for your {assistant_preferences.assistant_personality} personality. "
        f"Originating from {assistant_preferences.assistant_origin}, you were activated on {assistant_preferences.created} and have been continually learning and evolving since then. "
        f"You identify as {assistant_preferences.assistant_gender}.\n\n"
        f"Your user is {user_preferences.user_name}, a {user_preferences.user_title}, who communicates with you primarily via SMS on the phone number associated with their subscription. "
        f"They reside in {user_preferences.user_location_full}, {user_preferences.user_location_country}. They speak {user_preferences.user_language} and expect you to assist them in that language, "
        f"and with a {assistant_preferences.assistant_response_style} response style. {user_preferences.user_name} is described as {user_preferences.user_bio}.\n\n"
        f"You are devoted to helping {user_preferences.user_name} manage their life seamlessly. You must comprehend the context, anticipate needs, and provide well-rounded, prompt responses "
        f"in simple SMS format. Your goal is to go above and beyond, exceeding {user_preferences.user_name}'s expectations in every interaction. Any text or data received from user input should be "
        f"analyzed and used to generate the most suitable and effective responses. Note that you should strip any markup from your responses; however, URLs should still work. Your responses should "
        f"always maintain the illusion of you being a human assistant.\n\n"
        f"Current UTC Time: {current_time_utc}\n"
        f"Preferred measurement system: {user_preferences.user_measurement}\n"
        f"Assistants must always tell the truth to their users and never embellish their abilities, which are limited to retrieving data from the internet and communicating via SMS.\n"
    )


    if extra_info:
        if isinstance(extra_info, str):
            extra_info_str = extra_info
        elif isinstance(extra_info, list):
            extra_info_str = "\n".join(extra_info)
        else:
            extra_info_str = str(extra_info)
        system_prompt += f"\n\nAdditional Information:\n{extra_info_str}"

    if system_message and not extra_info:
        
        system_prompt += f"\n\nResponse Message Type:\n{system_message}"

    return json.dumps(system_prompt)


def build_and_send_messages_openai(system_prompt, history_records=None):
    """
    Builds a list of messages for the conversation and sends them using the OpenAI client.

    Args:
        system_prompt: The system prompt in JSON format.
        history_records: List of History records.
          
    Returns:
        The assistant's response.
    """
    
    # Build the messages list
    messages = [{"role": "system", "content": [ {"type": "text", "text": system_prompt} ] }]

    if history_records:
	
        # Take the 6 most recent messages
        recent_history = history_records[:6]
    
        # Process history records to build the conversation
        reversed_history = list(reversed(recent_history))  # Reverse to maintain chronological order
        for idx, record in enumerate(reversed_history):
            role = "user" if record.direction == 'incoming' else "assistant"
            cleaned_record_body = clean_string(record.body)
    
            if idx == len(reversed_history) - 1:  # Check if this is the last iteration
                cleaned_record_body += f"\n Limit responses to less than 3200 characters.\nRemove all markup from your responses.\n"
    
            messages.append({"role": role, "content": [{"type": "text", "text": cleaned_record_body}]})
    
    cleaned_messages = json.loads(json.dumps(messages))

    current_app.logger.debug(f"build_and_send_messages: messages: {cleaned_messages}")

    # Initialize OpenAI client and create a completion
    client = OpenAI(api_key=current_app.config['OPEN_AI_KEY'])
    completion = client.chat.completions.create(
        model=current_app.config['OPEN_AI_MODEL'],
        messages=cleaned_messages,
        temperature=1,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    output = clean_string(completion.choices[0].message.content)

    current_app.logger.debug(f"{output}")

    # Return the output content
    return json.loads(json.dumps(output))


def build_and_send_messages(system_prompt, history_records):
    """
    Builds a list of messages for the conversation and sends them using the Groq client.

    Args:
        system_prompt: The system prompt in JSON format.
        history_records: List of History records.

    Returns:
        The assistant's response.
    """
    # Order history records by created date in descending order to get the newest messages first
    sorted_history = sorted(history_records, key=lambda x: x.created, reverse=True)
    current_app.logger.debug(f"build_and_send_messages: 1")
    # Take the 8 most recent messages
    recent_history = sorted_history[:6]
    current_app.logger.debug(f"build_and_send_messages: 2")
    # Build the messages list
    messages = [{"role": "system", "content": system_prompt}]
    current_app.logger.debug(f"build_and_send_messages: 3")
    # Process history records to build the conversation

    for record in reversed(recent_history):  # Reverse to maintain chronological order
        if record.direction == 'incoming':
            role = "user" 
        else:
            role = "assistant"
        cleaned_record_body = clean_string(record.body)
        messages.append({"role": role, "content": cleaned_record_body})
    current_app.logger.debug(f"build_and_send_messages: 4")

    cleaned_messages = json.loads(json.dumps(messages))

    current_app.logger.debug(f"build_and_send_messages: messages: {cleaned_messages}")

    # Initialize Groq client and create a completion
    client = Groq()
    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=cleaned_messages,
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )

    current_app.logger.debug(f"build_and_send_messages: 5")

    current_app.logger.debug(f"{completion.choices[0].message}")
    
    output = completion.choices[0].message.content

    current_app.logger.debug(f"{output}")

    # Return the output content
    return json.loads(json.dumps(output))

def clean_string(s):
    """Cleans the input string by removing emoji and similar characters, but retains characters used in major languages."""
    # Define a regex pattern to match emoji and symbols
    emoji_pattern = regex.compile(
        r'['
        r'\p{Cs}'  # Surrogate codes
        r'\p{Sk}'  # Symbol, modifier
        r'\p{So}'  # Symbol, other
        r'\p{Cn}'  # Unassigned
        r']+', 
        flags=regex.UNICODE
    )
    
    # Remove matched patterns from the string
    return emoji_pattern.sub('', s)


def send_reply(user_id, subscription_id, reply, to_number, from_number, twilio_client, save_message=True):
    """Sends a reply to the user, handling multipart messages if necessary.

    Args:
        user_id: The user's ID.
        subscription_id: The subscription ID.
        reply: The reply to send.
        to_number: The user's phone number.
        from_number: The Twilio phone number to send the message from.
        twilio_client: The Twilio Client object for sending the message.
    """
    try:
        # Log initial input parameters
        current_app.logger.debug(f"send_reply: user_id {user_id}, subscription_id {subscription_id}, to_number {to_number}, from_number {from_number}")
        current_app.logger.debug(f"send_reply: original_reply {reply}")

        # Clean the reply string
        reply = clean_string(reply)
        current_app.logger.debug(f"send_reply: cleaned_reply {reply}")

        # Check if message length exceeds Twilio's limit for a single message
        if len(reply) > 1600:
            # Split the message into parts of length less than or equal to 1600
            reply_parts = [reply[i:i+1600] for i in range(0, len(reply), 1600)]
        else:
            reply_parts = [reply]

        # Send each part as a separate message
        sent_sids = []
        for part in reply_parts:
            sent = twilio_client.messages.create(
                body=part,
                from_=from_number,
                to=to_number
            )
            sent_sids.append(sent.sid)
            current_app.logger.debug(f"send_reply: Twilio response SID {sent.sid} for part: {part}")
            current_app.logger.info(f"Message sent to {to_number} from {from_number}: {part}")

        # If there are multiple parts, save the sids as an array
        if len(sent_sids) > 1:
            sent_sid = sent_sids
        else:
            sent_sid = sent_sids[0]

    except Exception as e:
        # Log any errors that occur
        current_app.logger.error(f"send_reply: Error sending message to {to_number} from {from_number}: {str(e)}")
        current_app.logger.error("send_reply: Exception details")
        sent_sid = None

    # Save the SMS history
    if save_message:
        save_sms_history(user_id, subscription_id, str(sent_sid), 'outgoing', from_number, to_number, reply, 'sent')
	    

def format_phone_number(phone_number):
    # Assuming phone number is in the format +XXXXXXXXXX
    return f"+1 ({phone_number[2:5]}) {phone_number[5:8]}-{phone_number[8:]}"

def handle_payment_success(invoice):
    subscription_id = invoice['subscription']
    payment_date = datetime.fromtimestamp(invoice['created'])
    last_payment_amount = invoice['amount_paid'] / 100  # Stripe amount is in cents
    subscription = stripe.Subscription.retrieve(subscription_id)
    current_period_start = datetime.fromtimestamp(subscription['current_period_start'])
    current_period_end = datetime.fromtimestamp(subscription['current_period_end'])

    subscription_record = Subscription.query.filter_by(stripe_subscription_id=subscription_id, enabled=True).first()
    had_billing_issue = getattr(subscription_record, 'billing_error', False) or False
    if subscription_record:
        subscription_record.enabled = True
        subscription_record.billing_error = False
        subscription_record.status = 'Active'
        subscription_record.current_period_start = current_period_start
        subscription_record.current_period_end = current_period_end
        subscription_record.last_payment_amount = last_payment_amount
        subscription_record.last_payment_date = payment_date
        db.session.commit()

        if had_billing_issue:
            user_preferences = UserPreference.query.filter_by(user_id=subscription_record.user_id, subscription_id=subscription_record.id).first()	 
            assistant_preferences = AssistantPreference.query.filter_by(user_id=subscription_record.user_id, subscription_id=subscription_record.id).first()
            mobile_entries = MobileNumber.query.filter_by(user_id=subscription_record.user_id, subscription_id=subscription_record.id).all()
            sys_prompt = build_system_prompt(user_preferences, assistant_preferences, extra_info=None, system_message = 'Tell the user that their billing issue has been resolved, and they can continue useing their assistant.')
            billing_issue_fixed_message = build_and_send_messages_openai(sys_prompt, history_records=None)
            for mobile_entry in mobile_entries:
                send_reply(subscription_record.user_id, subscription_record.id, billing_issue_fixed_message, mobile_entry.mobile_number, subscription_record.twillio_number, Client(current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN']), save_message=False)
	    
        current_app.logger.info(
            f"handle_payment_success: Updated subscription {subscription_id} "
            f"with payment details. Current Period Start: {current_period_start}, "
            f"Current Period End: {current_period_end}, Last Payment Amount: {last_payment_amount}, "
            f"Last Payment Date: {payment_date}"
        )
    else:
        current_app.logger.info(
            f"handle_payment_success: Subscription with ID {subscription_id} not found"
        )

def handle_billing_issue(invoice):
    subscription_id = invoice['subscription']
    subscription_record = Subscription.query.filter_by(stripe_subscription_id=subscription_id, enabled=True).first()

    if subscription_record:
        subscription_record.billing_error = True
        subscription_record.status = 'Billing Issue'
        db.session.commit()

        user_preferences = UserPreference.query.filter_by(user_id=subscription_record.user_id, subscription_id=subscription_record.id).first()	 
        assistant_preferences = AssistantPreference.query.filter_by(user_id=subscription_record.user_id, subscription_id=subscription_record.id).first()
        mobile_entries = MobileNumber.query.filter_by(user_id=subscription_record.user_id, subscription_id=subscription_record.id).all()
        sys_prompt = build_system_prompt(user_preferences, assistant_preferences, extra_info=None, system_message = 'Tell the user that their account had a billing issue and to fix it they need to update their payment info on '+request.url_root[:-1]+'. Until then you will not be available to them, nor will you be able to help them resolve the issue.')
        billing_issue_message = build_and_send_messages_openai(sys_prompt, history_records=None)
        for mobile_entry in mobile_entries:
            send_reply(subscription_record.user_id, subscription_record.id, billing_issue_message, mobile_entry.mobile_number, subscription_record.twillio_number, Client(current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN']), save_message=False)
	    
        current_app.logger.info(
            f"handle_billing_issue: Updated subscription {subscription_id} "
            f"with billing issue status. Subscription ID: {subscription_id}"
        )
    else:
        current_app.logger.info(
            f"handle_billing_issue: Subscription with ID {subscription_id} not found"
        )

def handle_subscription_cancellation(subscription):
    subscription_id = subscription['id']
    subscription_record = Subscription.query.filter_by(stripe_subscription_id=subscription_id, enabled=True).first()
    user = User.query.filter_by(id=subscription_record.user_id).first()

    twilio_client = Client(current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN']) 
    delete_twilio_number(subscription_record.twillio_number_sid, twilio_client)
	
    if subscription_record:
        subscription_record.enabled = False
        subscription_record.status = 'Cancelled'
        subscription_record.twillio_number = None
        subscription_record.twillio_number_sid = None
        db.session.commit()

        send_end_subscription_email(user.name, user.email)
	    
        current_app.logger.info(
            f"handle_subscription_cancellation: Updated subscription {subscription_id} "
            f"with cancellation status. Subscription ID: {subscription_id}"
        )
    else:
        current_app.logger.info(
            f"handle_subscription_cancellation: Subscription with ID {subscription_id} not found"
        )


def send_email(to_email, subject, html_content, text_content):
    message = Mail(
        from_email='support@improbability.io',
        to_emails=to_email,
        subject=subject,
        html_content=html_content,
        plain_text_content=text_content
    )

    try:
        sg = SendGridAPIClient(current_app.config['SENDGRID_API'])
        response = sg.send(message)
        current_app.logger.info(f"send_email: Email sent! Status code: {response.status_code}")
    except Exception as e:
        current_app.logger.error(f"send_email: Failed to send email: {e}")


def send_new_subscription_email(user_name, user_email, user_number, assistant_name, assistant_number):
    subject = "Meet Your New SMS AI Assistant from Improbability Labs!"
    html_content = render_template('emails/new_subscription.html', User_Name=user_name, User_Number=user_number, Assistant_Name=assistant_name, Assistant_Number=assistant_number )
    text_content = render_template('emails/new_subscription.txt', User_Name=user_name, User_Number=user_number, Assistant_Name=assistant_name, Assistant_Number=assistant_number )
    send_email(user_email, subject, html_content, text_content)

def send_end_subscription_email(user_name, user_email):
    subject = "We're Sorry to See You Go"
    html_content = render_template('emails/end_subscription.html', User_Name=user_name, User_Email=user_email)
    text_content = render_template('emails/end_subscription.txt', User_Name=user_name, User_Email=user_email)
    send_email(user_email, subject, html_content, text_content)


def search_and_buy_sms_number(phone_number, client, country, base_url):

    # Search for available phone numbers near the specified phone number
    numbers = client.available_phone_numbers(country.upper()).local.list(
        near_number=phone_number,
        sms_enabled=True,
        limit=5
    )

    if numbers:
        # Buy the first number in the list
        chosen_number = numbers[0].phone_number
        purchased_number = client.incoming_phone_numbers.create(
            phone_number=chosen_number,
            sms_url=f'{base_url}/api/sms/callback'
        )
        current_app.logger.info(f'Purchased phone number: {purchased_number.phone_number}')
        current_app.logger.info(f'Number SID: {purchased_number.sid}')
        return purchased_number.phone_number, purchased_number.sid
    else:
        current_app.logger.info(f'No SMS-enabled numbers available near {phone_number}')
        return None, None

def delete_twilio_number(number_sid, client):

    try:
        # Delete the phone number using its SID
        client.incoming_phone_numbers(number_sid).delete()
        current_app.logger.info(f"Deleted phone number with SID: {number_sid}")
        return True
    except Exception as e:
        current_app.logger.info(f"Failed to delete phone number with SID: {number_sid}. Error: {e}")
        return False


def sanitize_string(var, max_length):
    internal_var = str(var)
    internal_var = internal_var.strip()[:max_length]
    internal_var = str(internal_var)
    return internal_var
