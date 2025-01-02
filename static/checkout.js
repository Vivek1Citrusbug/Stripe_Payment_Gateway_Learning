// const stripe = Stripe("pk_test_51QcKmeF0OThiE2e46D1uIDNsXL7Ma16h8qYfZ266BzyO2SEvHHctSYhteclYuPZG5gR2DRm7QfTgqYBLuGY8So8L00pSsqzaNt"); // Replace with your publishable API key

// const options = {
//     mode: 'payment',
//     amount: 500,
//     currency: 'usd',
//     paymentMethodCreation: 'manual',
//     // Fully customizable with appearance API.
//     appearance: {/*...*/ },
// };

// // Set up Stripe.js and Elements to use in checkout form
// const elements = stripe.elements(options);

// // Create and mount the Payment Element
// const paymentElementOptions = { layout: 'accordion' };
// const paymentElement = elements.create('payment', paymentElementOptions);
// paymentElement.mount('#card-element');

// const form = document.getElementById('payment-form');
// const submitBtn = document.getElementById('submit');

// const handleError = (error) => {
//     const messageContainer = document.querySelector('#error-message');
//     messageContainer.textContent = error.message;
//     submitBtn.disabled = false;
// }

// form.addEventListener('submit', async (event) => {
//     // We don't want to let default form submission happen here,
//     // which would refresh the page.
//     event.preventDefault();

//     // Prevent multiple form submissions
//     if (submitBtn.disabled) {
//         return;
//     }

//     // Disable form submission while loading
//     submitBtn.disabled = true;

//     // Trigger form validation and wallet collection
//     const { error: submitError } = await elements.submit();
//     if (submitError) {
//         handleError(submitError);
//         return;
//     }

//     // Create the ConfirmationToken using the details collected by the Payment Element
//     // and additional shipping information
//     const { error, confirmationToken } = await stripe.createConfirmationToken({
//         elements,
//         // params: {
//         //     // shipping: {
//         //     //     name: 'Jenny Rosen',
//         //     //     address: {
//         //     //         line1: '1234 Main Street',
//         //     //         city: 'San Francisco',
//         //     //         state: 'CA',
//         //     //         country: 'US',
//         //     //         postal_code: '94111',
//         //     //     },
//         //     // },
//         //     return_url: 'https://example.com/order/123/complete'
//         // }
//     });

//     if (error) {
//         // This point is only reached if there's an immediate error when
//         // creating the ConfirmationToken. Show the error to your customer (for example, payment details incomplete)
//         handleError(error);
//         return;
//     }

//     // Create the PaymentIntent
//     const res = await fetch("/auth/subscribe/", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({
//             confirmationTokenId: confirmationToken.id,
//         }),
//     });

//     const data = await res.json();

//     // Handle any next actions or errors. See the Handle any next actions step for implementation.
//     handleServerResponse(data);
// });





// document.addEventListener("DOMContentLoaded", async () => {
//     const stripe = Stripe("pk_test_51QcKmeF0OThiE2e46D1uIDNsXL7Ma16h8qYfZ266BzyO2SEvHHctSYhteclYuPZG5gR2DRm7QfTgqYBLuGY8So8L00pSsqzaNt"); 
//     const form = document.getElementById("payment-form");
//     const submitButton = document.getElementById("submit");
//     const messageDiv = document.getElementById("error-message");

//     console.log("inside script")
//     console.log(stripe)
//     // Handle form submission
//     form.addEventListener("submit", async (event) => {
//         event.preventDefault();
//         submitButton.disabled = true;
//         messageDiv.textContent = "Processing payment...";

//         try {
//             // Create a payment intent on the server
//             const response = await fetch("/subscribe", { method: "POST" });
//             const { client_secret } = await response.json();

//             // Confirm the payment
//             const result = await stripe.confirmCardPayment(client_secret, {
//                 payment_method: {
//                     card: stripe.elements().create("card").mount("#card-element"),
//                 },
//             });

//             if (result.error) {
//                 messageDiv.textContent = `Payment failed: ${result.error.message}`;
//                 submitButton.disabled = false;
//             } else if (result.paymentIntent.status === "succeeded") {
//                 messageDiv.textContent = "Payment successful!";
//             }
//         } catch (error) {
//             console.error(error);
//             messageDiv.textContent = "An error occurred during payment processing.";
//             submitButton.disabled = false;
//         }
//     });
// });


document.addEventListener("DOMContentLoaded", async () => {
    const stripe = Stripe("pk_test_51QcKmeF0OThiE2e46D1uIDNsXL7Ma16h8qYfZ266BzyO2SEvHHctSYhteclYuPZG5gR2DRm7QfTgqYBLuGY8So8L00pSsqzaNt");
    const options = {
        mode: 'payment',
        amount: 500,
        currency: 'usd',
        paymentMethodCreation: 'manual',
        // Fully customizable with appearance API.
        appearance: {/*...*/ },
    };
    const elements = stripe.elements(options);
    const paymentElementOptions = { layout: 'tabs' };
    const paymentElement = elements.create('payment', paymentElementOptions);
    
    paymentElement.mount("#card-element");
    const form = document.getElementById("payment-form");
    const submitButton = document.getElementById("submit");
    const messageDiv = document.getElementById("error-message");

    // Handle form submission
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        submitButton.disabled = true;
        messageDiv.textContent = "Processing payment...";

        try {
            const response = await fetch("/auth/subscribe/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
            });
            console.log(response)
            if (!response.ok) {
                throw new Error("Failed to create Payment Intent");
            }

            const { client_secret } = await response.json();
            const result = await stripe.confirmPayment(client_secret, {
                elements,
                confirmParams: {
                    return_url: "http://127.0.0.1:8000/success", // Add your success page URL
                },
            });
            console.log(result)
            if (result.error) {
                messageDiv.textContent = `Payment failed: ${result.error.message}`;
            } else if (result.paymentIntent && result.paymentIntent.status === "succeeded") {
                messageDiv.textContent = "Payment successful!";
            }
        } catch (error) {
            console.error(error);
            messageDiv.textContent = "An error occurred during payment processing.";
        } finally {
            submitButton.disabled = false;
        }
    });
});

