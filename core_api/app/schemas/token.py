from pydantic import BaseModel
from typing import Optional

# --- Token Schemas ---

# Schema for the access token response
class Token(BaseModel):
    access_token: str
    token_type: str

# Schema for the data embedded within the JWT token
class TokenPayload(BaseModel):
    sub: Optional[int] = None # Subject (usually user ID)
    # Add other fields you might include in the token payload, e.g., roles, expiry 