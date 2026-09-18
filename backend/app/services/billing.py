"""
Stripe billing integration for the Premium subscription tier.

Follows the exact same graceful-degradation pattern as the Gemini
integration: if STRIPE_SECRET_KEY isn't configured, checkout/portal calls
return a clearly-labeled "preview mode" response instead of throwing, so
the rest of the app (and the frontend Billing page) keeps working for
demos and development without requiring a real Stripe account.
"""
from __future__ import annotations

from app.core.config import settings

PREMIUM_PRICE_USD = 9.99


def is_stripe_configured() -> bool:
    return bool(settings.STRIPE_SECRET_KEY)


def create_checkout_session(user_email: str, success_url: str, cancel_url: str) -> dict:
    if not is_stripe_configured():
        return {
            "preview_mode": True,
            "checkout_url": None,
            "message": (
                "Billing is running in preview mode (no STRIPE_SECRET_KEY configured). "
                "In production this would redirect to a real Stripe Checkout session."
            ),
        }

    try:
        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer_email=user_email,
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": "MedVision AI Premium"},
                        "unit_amount": int(PREMIUM_PRICE_USD * 100),
                        "recurring": {"interval": "month"},
                    },
                    "quantity": 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return {"preview_mode": False, "checkout_url": session.url, "session_id": session.id}
    except Exception as exc:
        return {"preview_mode": True, "checkout_url": None, "message": f"Stripe error: {exc}"}


def cancel_subscription(stripe_subscription_id: str | None) -> dict:
    if not is_stripe_configured() or not stripe_subscription_id:
        return {"preview_mode": True, "message": "No active Stripe subscription to cancel (preview mode)."}
    try:
        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.Subscription.cancel(stripe_subscription_id)
        return {"preview_mode": False, "message": "Subscription cancelled."}
    except Exception as exc:
        return {"preview_mode": True, "message": f"Stripe error: {exc}"}
