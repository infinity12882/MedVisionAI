from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.platform import Subscription, SubscriptionTier
from app.models.user import User
from app.schemas.extended import CheckoutSessionOut, SubscriptionOut
from app.services.billing import cancel_subscription, create_checkout_session, is_stripe_configured

router = APIRouter(prefix="/billing", tags=["Billing & Subscriptions"])


def _get_or_create_subscription(db: Session, user_id: str) -> Subscription:
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if sub is None:
        sub = Subscription(user_id=user_id, tier=SubscriptionTier.FREE)
        db.add(sub)
        db.commit()
        db.refresh(sub)
    return sub


@router.get("/subscription", response_model=SubscriptionOut)
def get_subscription(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sub = _get_or_create_subscription(db, current_user.id)
    return SubscriptionOut(
        tier=sub.tier, current_period_end=sub.current_period_end, is_stripe_configured=is_stripe_configured()
    )


@router.post("/checkout", response_model=CheckoutSessionOut)
def start_checkout(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = create_checkout_session(
        user_email=current_user.email,
        success_url="https://example.com/billing/success",
        cancel_url="https://example.com/billing/cancel",
    )
    if result.get("preview_mode"):
        # Demo convenience: instantly grant premium in preview mode so the feature is fully
        # demoable without a real Stripe account. Remove this in a production deployment —
        # real activation should only happen via the Stripe webhook handler below.
        sub = _get_or_create_subscription(db, current_user.id)
        sub.tier = SubscriptionTier.PREMIUM
        db.commit()
    return CheckoutSessionOut(**result)


@router.post("/cancel")
def cancel(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sub = _get_or_create_subscription(db, current_user.id)
    result = cancel_subscription(sub.stripe_subscription_id)
    sub.tier = SubscriptionTier.FREE
    db.commit()
    return result


from fastapi import Request, HTTPException
from app.core.config import settings

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Real deployments register this URL with Stripe and verify the
    signature using STRIPE_WEBHOOK_SECRET, then update the matching
    Subscription row based on `checkout.session.completed` /
    `customer.subscription.deleted` events. Left as an integration point.
    """
    import stripe
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    
    if not sig_header or not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="Missing signature or webhook secret")
        
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object']
        customer_email = session_obj.get("customer_email")
        if customer_email:
            user = db.query(User).filter(User.email == customer_email).first()
            if user:
                sub = _get_or_create_subscription(db, user.id)
                sub.tier = SubscriptionTier.PREMIUM
                db.commit()
                
    return {"status": "success"}
