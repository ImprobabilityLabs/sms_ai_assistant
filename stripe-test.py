import stripe

# Set your secret API key
stripe.api_key = 'sk_test_51OOwrOJzClWbuS5HbeOiB4hGSxENLt6wtU93hCrnSlM8PrMEN11AZBm0S6AigVgmuO9WfarMNe9VMlkszF5EN3CY00V9s7MIBt'

# Retrieve all products
products = stripe.Product.list(limit=10)  # Adjust limit as necessary

for product in products.auto_paging_iter():
    # Retrieve prices associated with the product
    prices = stripe.Price.list(product=product.id, type='recurring')

    for price in prices.data:
        # Access price fields
        price_id = price.id
        amount = price.unit_amount
        currency = price.currency.upper()
        interval = price.recurring.interval

        # Access product details
        description = product.description or "No description provided"
        
        # Extract feature names from the features and marketing_features
        features = [feature['name'] for feature in product.get('features', [])]
        marketing_features = [feature['name'] for feature in product.get('marketing_features', [])]

        # Handle the image URL
        images = product.images
        image_url = images[0] if images else 'No image available'

        # Print the product and price details
        print(f"Product ID: {product.id}")
        print(f"Description: {description}")
        print(f"Price ID: {price_id}")
        print(f"Cost: {amount / 100:.2f}")
        print(f"Currency: {currency}")
        print(f"Billing interval: {interval}")
        print(f"Features: {', '.join(features)}")
        print(f"Marketing Features: {', '.join(marketing_features)}")
        print(f"Image URL: {image_url}")
        print("--------------------------------------------------")




