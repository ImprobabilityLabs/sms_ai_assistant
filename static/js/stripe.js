  var stripe = Stripe('pk_test_51OOwrOJzClWbuS5HiI3za4AH1nlNiu1ZqJZo6ATTSTdA36SIOM0yOtotS2iUR0x6XFg5vCibUaOnK2VX6EG2kQF200jcPkbwTA'); // Replace with your public key

  var elements = stripe.elements();

var style = {
   base: {
     color: "#32325d",
     fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
     fontSmoothing: "antialiased",
     fontSize: "16px",
     "::placeholder": {
       color: "#aab7c4"
     },
   },
   invalid: {
     color: "#fa755a",
     iconColor: "#fa755a"
   }
};

  // Create instances of the card elements
  var cardNumber = elements.create('cardNumber', {style: style});
  var cardExpiry = elements.create('cardExpiry', {style: style});
  var cardCvc = elements.create('cardCvc', {style: style});

  // Mount the Stripe elements in the corresponding div containers
  cardNumber.mount('#card-number-element');
  cardExpiry.mount('#card-expiry-element');
  cardCvc.mount('#card-cvc-element');

      
  // Handle form submission
  var form = document.getElementById('payment-form');
  form.addEventListener('submit', function(event) {
    event.preventDefault();

    stripe.createToken(cardNumber).then(function(result) {
      if (result.error) {
        // Show error in your form
        var errorElement = document.getElementById('card-errors');
        errorElement.textContent = result.error.message;
      } else {
        // Send the token to your server
        stripeTokenHandler(result.token);
      }
    });
  });

  function stripeTokenHandler(token) {
    var form = document.getElementById('payment-form');
    var hiddenInput = document.createElement('input');
    hiddenInput.setAttribute('type', 'hidden');
    hiddenInput.setAttribute('name', 'stripeToken');
    hiddenInput.setAttribute('value', token.id);
    form.appendChild(hiddenInput);
    
    // Submit the form
    form.submit();
  }
