CREATE TABLE PAYMENTS (
    PAYMENT_ID NUMBER PRIMARY KEY,
    USER_ID NUMBER,
    RAZORPAY_ORDER_ID VARCHAR2(100),
    RAZORPAY_PAYMENT_ID VARCHAR2(100),
    RAZORPAY_SIGNATURE VARCHAR2(300),
    AMOUNT NUMBER(12,2),
    CURRENCY VARCHAR2(10),
    STATUS VARCHAR2(50),
    PAYMENT_METHOD VARCHAR2(50),
    CREATED_AT TIMESTAMP,
    UPDATED_AT TIMESTAMP
);

CREATE SEQUENCE PAYMENT_SEQ START WITH 1 INCREMENT BY 1;

CREATE TABLE USER_PREMIUM_STATUS (
    PREMIUM_ID NUMBER PRIMARY KEY,
    USER_ID NUMBER,
    IS_PREMIUM CHAR(1),
    PLAN_NAME VARCHAR2(100),
    START_DATE TIMESTAMP,
    END_DATE TIMESTAMP,
    CREATED_AT TIMESTAMP,
    UPDATED_AT TIMESTAMP
);

CREATE SEQUENCE PREMIUM_STATUS_SEQ START WITH 1 INCREMENT BY 1;
-------------------------------
from sqlalchemy import Column, Integer, Numeric, String, DateTime

from app.core.database import Base


class Payment(Base):
    __tablename__ = "PAYMENTS"

    payment_id = Column("PAYMENT_ID", Integer, primary_key=True)
    user_id = Column("USER_ID", Integer, nullable=False)
    razorpay_order_id = Column("RAZORPAY_ORDER_ID", String(100))
    razorpay_payment_id = Column("RAZORPAY_PAYMENT_ID", String(100))
    razorpay_signature = Column("RAZORPAY_SIGNATURE", String(300))
    amount = Column("AMOUNT", Numeric(12, 2))
    currency = Column("CURRENCY", String(10))
    status = Column("STATUS", String(50))
    payment_method = Column("PAYMENT_METHOD", String(50))
    created_at = Column("CREATED_AT", DateTime)
    updated_at = Column("UPDATED_AT", DateTime)
    -----------------------------------------------
    from sqlalchemy import Column, Integer, String, DateTime

from app.core.database import Base


class UserPremiumStatus(Base):
    __tablename__ = "USER_PREMIUM_STATUS"

    premium_id = Column("PREMIUM_ID", Integer, primary_key=True)
    user_id = Column("USER_ID", Integer, nullable=False)
    is_premium = Column("IS_PREMIUM", String(1))
    plan_name = Column("PLAN_NAME", String(100))
    start_date = Column("START_DATE", DateTime)
    end_date = Column("END_DATE", DateTime)
    created_at = Column("CREATED_AT", DateTime)
    updated_at = Column("UPDATED_AT", DateTime)
    -------------------------------
    from pydantic import BaseModel


class CreateOrderRequest(BaseModel):
    user_id: int
    plan_code: str = "PREMIUM_MONTHLY"


class VerifyPaymentRequest(BaseModel):
    user_id: int
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    -----------------------------
    from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.user_premium_status import UserPremiumStatus


class PaymentRepository:

    @staticmethod
    def get_payment_next_id(db: Session):
        result = db.execute(text("SELECT PAYMENT_SEQ.NEXTVAL FROM DUAL"))
        return result.scalar()

    @staticmethod
    def get_premium_next_id(db: Session):
        result = db.execute(text("SELECT PREMIUM_STATUS_SEQ.NEXTVAL FROM DUAL"))
        return result.scalar()

    @staticmethod
    def create_payment(db: Session, payment: Payment):
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def get_payment_by_order_id(db: Session, order_id: str):
        return (
            db.query(Payment)
            .filter(Payment.razorpay_order_id == order_id)
            .first()
        )

    @staticmethod
    def update_payment(db: Session, payment: Payment):
        payment.updated_at = datetime.now()
        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def get_premium_by_user(db: Session, user_id: int):
        return (
            db.query(UserPremiumStatus)
            .filter(UserPremiumStatus.user_id == user_id)
            .first()
        )

    @staticmethod
    def create_premium_status(db: Session, user_id: int, plan_name: str, start_date, end_date):
        premium = UserPremiumStatus(
            premium_id=PaymentRepository.get_premium_next_id(db),
            user_id=user_id,
            is_premium="Y",
            plan_name=plan_name,
            start_date=start_date,
            end_date=end_date,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.add(premium)
        db.commit()
        db.refresh(premium)
        return premium

    @staticmethod
    def update_premium_status(db: Session, premium: UserPremiumStatus, plan_name: str, start_date, end_date):
        premium.is_premium = "Y"
        premium.plan_name = plan_name
        premium.start_date = start_date
        premium.end_date = end_date
        premium.updated_at = datetime.now()

        db.commit()
        db.refresh(premium)
        return premium
        ---------------------------
        import hashlib
import hmac
from datetime import datetime, timedelta

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.payment import Payment
from app.repositories.payment_repository import PaymentRepository
from app.repositories.user_repository import UserRepository


PLANS = {
    "PREMIUM_MONTHLY": {
        "plan_name": "Premium Member",
        "amount_rupees": 99,
        "validity_days": 30
    }
}


class PaymentService:

    @staticmethod
    def create_order(db: Session, user_id: int, plan_code: str):
        user = UserRepository.get_by_id(db, user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if plan_code not in PLANS:
            raise HTTPException(status_code=400, detail="Invalid plan selected")

        plan = PLANS[plan_code]
        amount_paise = int(plan["amount_rupees"] * 100)

        payload = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"premium_{user_id}_{int(datetime.now().timestamp())}",
            "notes": {
                "user_id": str(user_id),
                "plan_code": plan_code
            }
        }

        response = requests.post(
            "https://api.razorpay.com/v1/orders",
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
            json=payload,
            timeout=20
        )

        if response.status_code not in [200, 201]:
            raise HTTPException(
                status_code=400,
                detail=f"Razorpay order creation failed: {response.text}"
            )

        order_data = response.json()

        payment = Payment(
            payment_id=PaymentRepository.get_payment_next_id(db),
            user_id=user_id,
            razorpay_order_id=order_data["id"],
            amount=plan["amount_rupees"],
            currency="INR",
            status="CREATED",
            payment_method="RAZORPAY",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        PaymentRepository.create_payment(db, payment)

        return {
            "key_id": settings.RAZORPAY_KEY_ID,
            "order_id": order_data["id"],
            "amount": amount_paise,
            "currency": "INR",
            "plan_code": plan_code,
            "plan_name": plan["plan_name"],
            "description": "BudgetPro Premium Membership"
        }

    @staticmethod
    def verify_payment(
        db: Session,
        user_id: int,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ):
        payment = PaymentRepository.get_payment_by_order_id(db, razorpay_order_id)

        if not payment:
            raise HTTPException(status_code=404, detail="Payment order not found")

        if int(payment.user_id) != int(user_id):
            raise HTTPException(
                status_code=403,
                detail="Payment does not belong to this user"
            )

        generated_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()

        if generated_signature != razorpay_signature:
            payment.status = "FAILED"
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            PaymentRepository.update_payment(db, payment)

            raise HTTPException(
                status_code=400,
                detail="Invalid Razorpay payment signature"
            )

        payment.status = "PAID"
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        PaymentRepository.update_payment(db, payment)

        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)

        existing_premium = PaymentRepository.get_premium_by_user(db, user_id)

        if existing_premium:
            premium = PaymentRepository.update_premium_status(
                db,
                existing_premium,
                "Premium Member",
                start_date,
                end_date
            )
        else:
            premium = PaymentRepository.create_premium_status(
                db,
                user_id,
                "Premium Member",
                start_date,
                end_date
            )

        return {
            "message": "Payment verified successfully",
            "user_id": user_id,
            "is_premium": True,
            "plan_name": premium.plan_name,
            "end_date": premium.end_date
        }

    @staticmethod
    def get_premium_status(db: Session, user_id: int):
        user = UserRepository.get_by_id(db, user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        premium = PaymentRepository.get_premium_by_user(db, user_id)

        if not premium:
            return {
                "user_id": user_id,
                "is_premium": False,
                "plan_name": None,
                "end_date": None
            }

        is_active = (
            premium.is_premium == "Y"
            and premium.end_date
            and premium.end_date >= datetime.now()
        )

        return {
            "user_id": user_id,
            "is_premium": bool(is_active),
            "plan_name": premium.plan_name if is_active else None,
            "end_date": premium.end_date if is_active else None
        }


payment_service = PaymentService()
-----------------------------------
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.payment.payment_schema import (
    CreateOrderRequest,
    VerifyPaymentRequest
)
from app.services.payment_service import payment_service


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/create-order")
def create_order(
    request: CreateOrderRequest,
    db: Session = Depends(get_db)
):
    return payment_service.create_order(
        db,
        request.user_id,
        request.plan_code
    )


@router.post("/verify-payment")
def verify_payment(
    request: VerifyPaymentRequest,
    db: Session = Depends(get_db)
):
    return payment_service.verify_payment(
        db,
        request.user_id,
        request.razorpay_order_id,
        request.razorpay_payment_id,
        request.razorpay_signature
    )


@router.get("/status/{user_id}")
def get_premium_status(
    user_id: int,
    db: Session = Depends(get_db)
):
    return payment_service.get_premium_status(db, user_id)
    ------------------------------
    