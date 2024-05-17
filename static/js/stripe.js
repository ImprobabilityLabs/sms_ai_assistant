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

    
