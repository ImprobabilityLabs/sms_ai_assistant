import os

class Config:
    LOG_PATH = os.getenv('LOG_PATH', "/var/log/improbability/")
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', 'False')
    if SQLALCHEMY_TRACK_MODIFICATIONS.upper() == "FALSE":
        SQLALCHEMY_TRACK_MODIFICATIONS = False
    else:
        SQLALCHEMY_TRACK_MODIFICATIONS = True	
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_AUTHORIZATION_URL = os.getenv('GOOGLE_AUTHORIZATION_URL')
    GOOGLE_TOKEN_URL = os.getenv('GOOGLE_TOKEN_URL')
    STRIPE_API_KEY = os.getenv('STRIPE_API_KEY')
    STRIPE_ENDPOINT_SECRET = os.getenv('STRIPE_ENDPOINT_SECRET')
    MICROSOFT_CLIENT_ID = os.getenv('MICROSOFT_CLIENT_ID')
    MICROSOFT_CLIENT_SECRET = os.getenv('MICROSOFT_CLIENT_SECRET')
    MICROSOFT_CLIENT_SECRET_ID = os.getenv('MICROSOFT_CLIENT_SECRET_ID')
    MICROSOFT_AUTHORIZATION_URL = os.getenv('MICROSOFT_AUTHORIZATION_URL')
    MICROSOFT_TOKEN_URL = os.getenv('MICROSOFT_TOKEN_URL')
    MICROSOFT_REDIRECT_URI = os.getenv('MICROSOFT_REDIRECT_URI')
    SEO_FOR_DATA_KEY = os.getenv('SEO_FOR_DATA_KEY')
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    GROQ_KEY = os.getenv('GROQ_KEY')
    OPEN_AI_KEY = os.getenv('OPEN_AI_KEY')
    OPEN_AI_MODEL = os.getenv('OPEN_AI_MODEL')
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    GOOGLE_ANALYTICS_ID = os.getenv('GOOGLE_ANALYTICS_ID')
    if GOOGLE_ANALYTICS_ID and GOOGLE_ANALYTICS_ID.upper() == 'NONE':
        GOOGLE_ANALYTICS_ID = None
    GOOGLE_SITE_VERIFICATION = os.getenv('GOOGLE_SITE_VERIFICATION')
    if GOOGLE_SITE_VERIFICATION and GOOGLE_SITE_VERIFICATION.upper() == 'NONE':
        GOOGLE_SITE_VERIFICATION = None
    BING_SITE_VERIFICATION = os.getenv('BING_SITE_VERIFICATION')
    if BING_SITE_VERIFICATION and BING_SITE_VERIFICATION.upper() == 'NONE':
        BING_SITE_VERIFICATION = None
