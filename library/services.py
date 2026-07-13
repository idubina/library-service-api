import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_session(borrowing, money_to_pay):
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": borrowing.book.title,
                    },
                    "unit_amount": int(money_to_pay * 100),
                },
                "quantity": 1,
            }
        ],
        success_url=(
            "http://localhost:8000/api/library/payments/success/"
            "?session_id={CHECKOUT_SESSION_ID}"
        ),
        cancel_url="http://localhost:8000/api/library/payments/cancel/",
    )

    return session
