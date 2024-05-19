import requests
import json
from groq import Groq
import sys
import re
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort, current_app
from models import db, User, Subscription, MobileNumber, History, UserPreference, AssistantPreference 
from twilio.request_validator import RequestValidator
from flask_sqlalchemy import SQLAlchemy
from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session
#from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY, SQLALCHEMY_DATABASE_URI, STRIPE_API_KEY, MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, MICROSOFT_AUTHORIZATION_URL, MICROSOFT_TOKEN_URL, MICROSOFT_CLIENT_SECRET_ID, MICROSOFT_REDIRECT_URI
#from werkzeug.middleware.proxy_fix import ProxyFix
import requests
import stripe
import os
from datetime import datetime

seo_for_data_auth = "cmFoaW1rQGltcHJvYmFiaWxpdHkuaW86NGQ4MzY1OWQ4YWEyNTIwNQ=="

def remove_keys(data, keys_to_remove):
    """ Recursively remove specified keys from a dictionary. """
    if isinstance(data, dict):
        return {key: remove_keys(value, keys_to_remove) for key, value in data.items() if key not in keys_to_remove}
    elif isinstance(data, list):
        return [remove_keys(item, keys_to_remove) for item in data]
    else:
        return data

def fetch_data(question):
    """ Fetch data from the DataForSEO API for the specified question. """
    url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
    payload = json.dumps([{
        "keyword": question,
        "location_code": 2840,
        "language_code": "en",
        "device": "desktop",
        "os": "windows",
        "depth": 1
    }])
    headers = {
        'Authorization': f"Basic {seo_for_data_auth}",
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, data=payload)
    data = response.json()
    return data['tasks'][0]['result']

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

def answer_question(question, data):
    client = Groq()
    completion = client.chat.completions.create(
        #model="mixtral-8x7b-32768",
        model="llama3-8b-8192",
        messages=[
            {
                "role": "system",
                "content": "Extract the answer to '"+question+"', and output it in a paragraph with any additional relevant information."
            },
            {
                "role": "user",
                "content": data
            }
        ],
        temperature=1,
        max_tokens=512,
        top_p=1,
        stream=False,
        stop=None,
    )

    return completion.choices[0].message.content

def extract_questions(message_text):
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
        max_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )

    print(f"Tokens: {completion.usage}")

    lines = completion.choices[0].message.content.split('\n')

    # Filter lines containing the question mark and clean them
    filtered_questions = [
        re.sub(r"[^a-zA-Z0-9? \[\]]", "", line) for line in lines if '?' in line
    ]

    return filtered_questions


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


def handle_stripe_operations(user, form_data):
    try:
        if not user.stripe_customer_id:
            # Raise an exception if the Stripe customer ID does not exist
            raise ValueError("Stripe customer ID not found for user.")

        # Retrieve the existing customer and update the billing information
        customer = stripe.Customer.retrieve(user.stripe_customer_id)
        customer.name = form_data['card-name']
        customer.email = user.email
        customer.address = {
            'line1': form_data['billing-address'],
            'country': form_data['billing-country'],
            'state': form_data['billing-state'],
            'postal_code': form_data['billing-zip'],
        }
        customer.save()

        # Convert token to PaymentMethod and attach it to the customer
        payment_method = stripe.PaymentMethod.create(
            type="card",
            card={"token": form_data['stripeToken']},
            billing_details={
                'name': form_data['card-name'],
                'email': user.email, 
                'address': {
                    'line1': form_data['billing-address'],
                    'country': form_data['billing-country'],
                    'state': form_data['billing-state'],
                    'postal_code': form_data['billing-zip'],
                }
            }
        )

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

        # Create or update the Stripe subscription
        subscription = stripe.Subscription.create(
            customer=user.stripe_customer_id,
            items=[{'price': form_data['subscriptionOption']}],
            expand=['latest_invoice.payment_intent', 'latest_invoice'],
        )

        # Check if the payment was successful
        payment_intent = subscription.latest_invoice.payment_intent
        if payment_intent.status != 'succeeded':
            # Delete the subscription if payment was not successful
            stripe.Subscription.delete(subscription.id)
            raise ValueError("Payment was not successful.")

        # Extract necessary fields from the subscription
        subscription_id = subscription.id
        current_period_start = datetime.utcfromtimestamp(subscription.current_period_start).strftime('%Y-%m-%d %H:%M:%S')
        current_period_end = datetime.utcfromtimestamp(subscription.current_period_end).strftime('%Y-%m-%d %H:%M:%S')
        status = subscription.status

        # Create a new Subscription record in the database
        new_subscription = Subscription(
            user_id=user.id,
            stripe_customer_id=user.stripe_customer_id,
            stripe_plan_id=subscription.plan.id,
            stripe_product_id=subscription.plan.product,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            status=status
        )

        # Add the new subscription to the database
        db.session.add(new_subscription)
        db.session.commit()

        # Update the user's subscription status in the database
        user.is_subscribed = True
        db.session.commit()

        current_app.logger.info('Subscription created successfully.')
        return True, None

    except stripe.error.StripeError as e:
        current_app.logger.error(f'Stripe error: {e.user_message}')
        return False, e.user_message
    except Exception as e:
        current_app.logger.error(f'Error: {str(e)}')
        return False, str(e)

# Assuming extract_questions(msg) returns a list of questions
#questions = extract_questions(msg)

# Iterate through the list and print each question
#for question in questions:
#    print("\n")
#    print("Question: " + question)
#    print("\n")
#    fetched_answer = fetch_data(question)
#    cleaned_answer = clean_data(fetched_answer)
#    answer = answer_question(question, cleaned_answer)
#    print("\nAnswer: " + answer)


# Check if at least one additional argument was passed
#if len(sys.argv) <= 1:
#    print("No location text was passed. Please run the script with a location argument.")
#    sys.exit()

#location_txt = sys.argv[1]

#client = Groq()
#completion = client.chat.completions.create(
#    model="llama3-8b-8192",
#    messages=[
#        {
#            "role": "system",
#            "content": "Convert the users input into a Location Full Text(City, State or Province, Country) and Country ISO Code( ISO 3166-1 alpha-2). If the location does not match, respond with null.\n\nRespond in a JSON Format with 2 fields (location_text, country_code) and no other text."
#        },
#        {
#            "role": "user",
#            "content": json.dumps(location_txt, indent=2)
#        }
#    ],
#    temperature=1,
#    max_tokens=128,
#    top_p=1,
#    stream=False,
#    stop=None,
#)
#print(f"Tokens: {completion.usage}")
#output = completion.choices[0].message.content
#print(output)
# Convert the string to a dictionary
#data_dict = json.loads(output)

# Now you can access the values by their keys
#location_text = data_dict['location_text']
#country_code = data_dict['country_code']

#print("Location Text:", location_text)
#print("Country Code:", country_code)


