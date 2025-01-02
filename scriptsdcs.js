const stripe = Stripe("pk_test_51QcKmeF0OThiE2e46D1uIDNsXL7Ma16h8qYfZ266BzyO2SEvHHctSYhteclYuPZG5gR2DRm7QfTgqYBLuGY8So8L00pSsqzaNt"); // Replace with your publishable API key

stripe.confirmCardPayment(clientSecret, {
    payment_method: {
        card: cardElement, // Card details collected with Stripe Elements
        billing_details: {
            name: 'Customer Name',
        },
    },
}).then(function (result) {
    if (result.error) {
        // Handle error (e.g., display error message to user)
        console.error(result.error.message);
    } else {
        if (result.paymentIntent.status === 'succeeded') {
            // Payment succeeded, proceed with backend updates
            console.log("Payment succeeded:", result.paymentIntent);
        }
    }
});
