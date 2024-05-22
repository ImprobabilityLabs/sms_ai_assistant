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


seo_for_data_auth = "cmFoaW1rQGltcHJvYmFiaWxpdHkuaW86NGQ4MzY1OWQ4YWEyNTIwNQ=="

def remove_keys(data, keys_to_remove):
    """ Recursively remove specified keys from a dictionary. """
    if isinstance(data, dict):
        return {key: remove_keys(value, keys_to_remove) for key, value in data.items() if key not in keys_to_remove}
    elif isinstance(data, list):
        return [remove_keys(item, keys_to_remove) for item in data]
    else:
        return data

def fetch_data_old(question, location=None):
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
        'Authorization': f"Basic {seo_for_data_auth}",
        'Content-Type': 'application/json'
    }
    
    # Configure retries and timeout
    retry_strategy = Retry(
        total=3,  # Total number of retries
        status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP status codes
        method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],  # Retry for these methods
        backoff_factor=1  # Exponential backoff factor
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    
    try:
        response = http.post(url, headers=headers, data=payload, timeout=10)  # Added timeout
        current_app.logger.debug(f"fetch_data() Position 1 - Response Status: {response.status_code}")
        response.raise_for_status()  # Raise HTTPError for bad responses
        current_app.logger.debug(f"fetch_data() Position 2 - Response Text: {response.text}")
        data = response.json()
        current_app.logger.debug(f"fetch_data() Position 3 - JSON Data: {data}")
        
        # Check if the response contains the expected data
        if 'tasks' in data and len(data['tasks']) > 0 and 'result' in data['tasks'][0]:
            return data['tasks'][0]['result']
        else:
            current_app.logger.warning("fetch_data() - No result found in the response")
            return None  # Or handle the case where the result is not found
    
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Request failed: {e}")
        current_app.logger.error("fetch_data() Request Exception Error")
        return None

    except json.JSONDecodeError:
        current_app.logger.error("fetch_data() JSONDecodeError - Failed to decode JSON response")
        return None

    except KeyError:
        current_app.logger.error("fetch_data() KeyError - Unexpected response structure")
        return None


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
        'Authorization': f"Basic {seo_for_data_auth}",
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
            "Authorization": "Bearer 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",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {
                    "role": "system",
                    "content": f"Extract the answer to '{question}', and output it in a paragraph with any additional relevant information."
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
        
def answer_question_old(question, data):
    current_app.logger.debug(f"answer_question - Question Input: {question}")
    try:
        client = Groq()
        completion = client.chat.completions.create(
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
            max_tokens=256,
            top_p=1,
            stream=False,
            stop=None,
        )
        current_app.logger.debug(f"answer_question() Position 1")
        return completion.choices[0].message.content
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
 
        # Conditionally apply tax rates based on the billing country
        tax_rate_ids = []
        if form_data['billing-country'] == 'CA':  # Check if the billing country is Canada
            # Retrieve the tax rate ID for Canada programmatically
            tax_rates = stripe.TaxRate.list(active=True)
            for tax_rate in tax_rates:
                if tax_rate.country == 'CA':
                    tax_rate_ids.append(tax_rate.id)
                    break

        # Create or update the Stripe subscription
        subscription = stripe.Subscription.create(
            customer=user.stripe_customer_id,
            items=[{'price': form_data['subscriptionOption']}],
            default_tax_rates=tax_rate_ids,
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

        subscription_id = new_subscription.id

        current_app.logger.info('Subscription created successfully.')
        return True, None, subscription_id

    except stripe.error.StripeError as e:
        current_app.logger.error(f'Stripe error: {e.user_message}')
        return False, e.user_message, -1
    except Exception as e:
        current_app.logger.error(f'Error: {str(e)}')
        return False, str(e), -1



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
            current_app.logger.debug(f"process_questions_answers() Position 4")
            answer = await answer_question(question, cleaned_answer)
            current_app.logger.debug(f"process_questions_answers() Position 5")
            current_app.logger.debug(f"Answer: {answer}")
            answers.append(answer)

        return answers
        
    except Exception as e:
        current_app.logger.error(f"Error in process_questions_answers: {e}")
        return None




def process_questions_answers_old(text_message, location, location_country = 'US'):

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
            fetched_answer = fetch_data(question, location_country)
            current_app.logger.debug(f"process_questions_answers() Position 3")
            cleaned_answer = clean_data(fetched_answer)
            current_app.logger.debug(f"process_questions_answers() Position 4")
            answer = answer_question(question, cleaned_answer)
            current_app.logger.debug(f"process_questions_answers() Position 5")
            current_app.logger.debug(f"Answer: {answer}")
            answers.append(answer)

        return answers
        
    except Exception as e:
        current_app.logger.error(f"Error in process_questions_answers: {e}")
        return None

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

        if not subscription:
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
    # Create a new History instance
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

    # Add the record to the session
    db.session.add(history_record)

    # Commit the session to the database
    try:
        db.session.commit()
        return True
    except Exception as e:
        # Handle any exceptions that occur during commit
        db.session.rollback()
        print(f"Error saving history record: {e}")
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

def build_system_prompt(user_preferences, assistant_preferences, extra_info=None):
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
        f"You are a virtual assistant named {assistant_preferences.assistant_name}, known for your {assistant_preferences.assistant_demeanor} demeanor, "
        f"{assistant_preferences.assistant_attitude} attitude, and {assistant_preferences.assistant_personality} personality. Originating from {assistant_preferences.assistant_origin}, "
        f"you were activated on {assistant_preferences.created} and have been continually learning and evolving since then. You identify as {assistant_preferences.assistant_gender}.\n\n"
        f"Your user is {user_preferences.user_name}, a {user_preferences.user_title}, who communicates with you primarily via SMS on the phone number associated with their subscription. "
        f"They reside in {user_preferences.user_location_full}, {user_preferences.user_location_country}. They speak {user_preferences.user_language} and expect you to assist them in that language, "
        f"and with a {assistant_preferences.assistant_response_style} response style. {user_preferences.user_name} is described as {user_preferences.user_bio}.\n\n"
        f"You are devoted to helping {user_preferences.user_name} manage their life seamlessly. You must comprehend the context, anticipate needs, and provide well-rounded, prompt responses "
        f"in simple SMS format. Your goal is to go above and beyond, exceeding {user_preferences.user_name}'s expectations in every interaction. Any text or data received from user input should be "
        f"analyzed and used to generate the most suitable and effective responses. Note that you should strip any markup from your responses; however, URLs should still work. Your responses should "
        f"always maintain the illusion of you being a human assistant.\n\n"
        f"Current UTC Time: {current_time_utc}\n"
        f"Preferred measurement system: {user_preferences.user_measurement}\n"
    )

    if extra_info:
        if isinstance(extra_info, str):
            extra_info_str = extra_info
        elif isinstance(extra_info, list):
            extra_info_str = "\n".join(extra_info)
        else:
            extra_info_str = str(extra_info)
        system_prompt += f"\n\nAdditional Information:\n{extra_info_str}"

    return json.dumps(system_prompt)

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
    recent_history = sorted_history[:5]
    current_app.logger.debug(f"build_and_send_messages: 2")
    # Build the messages list
    messages = [{"role": "system", "content": json.dumps(system_prompt, ensure_ascii=False)}]
    current_app.logger.debug(f"build_and_send_messages: 3")
    # Process history records to build the conversation
    current_app.logger.debug(f"build_and_send_messages: recent_history: {recent_history}")
    for record in reversed(recent_history):  # Reverse to maintain chronological order
        role = "user" if record.direction == 'inbound' else "assistant"
        messages.append({"role": role, "content": json.dumps(record.body, ensure_ascii=False)})
    current_app.logger.debug(f"build_and_send_messages: 4")

    current_app.logger.debug(f"build_and_send_messages: messages: {messages}")
    # Initialize Groq client and create a completion
    client = Groq()
    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=json.dumps(messages, ensure_ascii=False),
        temperature=1,
        max_tokens=2048,
        top_p=1,
        stream=False,
        stop=None,
    )
    current_app.logger.debug(f"build_and_send_messages: 5")

    current_app.logger.debug(f"messages: {messages}")

    output = completion.choices[0].message.content

    return json.loads(output)


def clean_string(s):
    """Cleans the input string by removing non-ASCII characters, except hyphens."""
    return "".join(c for c in s if c.isascii() and c != '\u2013' and c != '\u2014')


def send_reply(user_id, subscription_id, reply, to_number, from_number, twilio_client):
    """Sends a reply to the user.

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

        # Send the message and log the attempt
        sent = twilio_client.messages.create(
            body=reply,
            from_=from_number,
            to=to_number
        )

        # Log the Twilio response
        current_app.logger.debug(f"send_reply: Twilio response SID {sent.sid}")
        current_app.logger.info(f"Message sent to {to_number} from {from_number}: {reply}")

    except Exception as e:
        # Log any errors that occur
        current_app.logger.error(f"send_reply: Error sending message to {to_number} from {from_number}: {str(e)}")
        current_app.logger.error("send_reply: Exception details")

    save_sms_history(user_id, subscription_id, sent.sid, 'outgoing', from_number, to_number, sent.body, sent.status)
