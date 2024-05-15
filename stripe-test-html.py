import stripe

# Set your secret API key
stripe.api_key = 'sk_test_51OOwrOJzClWbuS5HbeOiB4hGSxENLt6wtU93hCrnSlM8PrMEN11AZBm0S6AigVgmuO9WfarMNe9VMlkszF5EN3CY00V9s7MIBt'

# Retrieve all products
products = stripe.Product.list(limit=10)  # Adjust limit as necessary

html_output = ""

for product in products.auto_paging_iter():
    # Retrieve prices associated with the product
    prices = stripe.Price.list(product=product.id, type='recurring')

    for price in prices.data:
        # Access price fields
        price_id = price.id
        amount = price.unit_amount
        currency = price.currency.upper()
        interval = price.recurring.interval
 
        # Retrieve product details including description
        description = product.description or "No description provided"  # Ensure description is defined

        # Access metadata
        country = product.metadata.get('country', '')  
        tax = float(product.metadata.get('tax', 0.0))
        tax_name = product.metadata.get('tax_name', '')  

        # Extract feature names from the features and marketing_features
        features = [feature['name'] for feature in product.get('features', [])]

        # Handle the image URL
        images = product.images
        image_url = images[0] if images else 'https://example.com/default-image.jpg'  # Default image if none available

        # Generate HTML
        html_output += f'''
        <div class="col-xs-12 col-sm-6">
          <div class="radio black-title">
            <label>
              <input type="radio" name="subscriptionOption" value="{product.id}" data-price-id="{price_id}" data-cost="{amount/100:.2f}" data-currency="{currency}" data-interval="{interval}" data-country="{country}" data-product="{product.name}" data-tax-percent="{tax:.2f}" data-tax-name="{tax_name}">
              <strong>{product.name}</strong>
              <img src="{image_url}" alt="{product.name} Image" style="height:20px; width:30px;">
            </label>
          </div>
          <p><strong>${amount / 100:.2f} {currency} / month</strong></p>
          <ul>\n'''
        for feature in features:
            html_output += f"            <li>{feature}</li>\n"
            
            html_output += f'''          </ul>
          <p>{description}</p>
        </div>'''

print(html_output)









