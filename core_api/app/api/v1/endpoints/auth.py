# core_api/app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field
import random
import string
from app.core import security
from app.db import redis_client
from app.crud import user as crud_user
from app.api import deps
from sqlalchemy.orm import Session

# TODO: Implement proper OTP generation, storage (e.g., Redis), and sending mechanism
# TODO: Implement proper JWT generation and handling
# TODO: Integrate with User CRUD operations

router = APIRouter()

# --- Schemas --- #
class OtpRequest(BaseModel):
    telegram_id: int = Field(..., description="The Telegram User ID")

class OtpVerify(BaseModel):
    telegram_id: int = Field(..., description="The Telegram User ID")
    otp: str = Field(..., min_length=6, max_length=6, description="The 6-digit OTP received by the user")

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Helper Functions (Placeholders) --- #
def generate_otp(length: int = 6) -> str:
    """Generates a simple numeric OTP."""
    return "".join(random.choices(string.digits, k=length))

async def send_otp_to_bot(telegram_id: int, otp: str):
    """Placeholder function to simulate sending OTP via the bot."""
    # In reality, this would make an HTTP request to a bot endpoint
    # or use a message queue (like RabbitMQ/Celery) to notify the bot.
    print(f"---> Sending OTP {otp} to Telegram user {telegram_id} (simulation)")
    # Simulate success for now
    return True

# --- API Endpoints --- #
@router.post("/request-otp", status_code=status.HTTP_200_OK)
async def request_otp(
    payload: OtpRequest,
    db: Session = Depends(deps.get_db)
):
    """
    Requests an OTP for a given Telegram ID.
    Checks user existence, generates OTP, stores it in Redis, and simulates sending it via bot.
    """
    # --- Check if user exists --- #
    db_user = crud_user.get_user_by_telegram_id(db, telegram_id=payload.telegram_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this Telegram ID not found. Please register via the bot first."
        )
    if not db_user.is_active:
         raise HTTPException(status_code=400, detail="Inactive user")

    otp = generate_otp()
    # --- Store OTP in Redis --- #
    await redis_client.set_otp(payload.telegram_id, otp)

    print(f"Generated OTP for {payload.telegram_id}: {otp}") # Log for debugging

    # Simulate sending OTP to the bot
    sent = await send_otp_to_bot(payload.telegram_id, otp)

    if not sent:
        # Cleanup OTP if sending failed
        await redis_client.delete_otp(payload.telegram_id)
        raise HTTPException(status_code=500, detail="Failed to send OTP via bot")

    return {"message": "OTP sent successfully via Telegram bot."}

@router.post("/verify-otp", response_model=Token)
async def verify_otp(
    payload: OtpVerify,
    db: Session = Depends(deps.get_db)
):
    """
    Verifies the OTP provided by the user (retrieved from Redis) and returns a JWT token upon success.
    """
    # --- Get OTP from Redis (and delete it) --- #
    stored_otp = await redis_client.get_otp(payload.telegram_id)

    if not stored_otp or stored_otp != payload.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )

    # --- OTP is valid --- #

    # --- Get User from DB (we know user exists from request_otp) --- #
    db_user = crud_user.get_user_by_telegram_id(db, telegram_id=payload.telegram_id)
    if not db_user: # Should ideally not happen if request_otp worked
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found despite valid OTP. Please contact support.",
        )
    if not db_user.is_active:
        # Double check active status
        raise HTTPException(status_code=400, detail="User is inactive.")

    # --- Generate JWT Token --- #
    access_token = security.create_access_token(
        subject=db_user.id # Use the database user ID as the token subject
    )

    return {"access_token": access_token, "token_type": "bearer"} 