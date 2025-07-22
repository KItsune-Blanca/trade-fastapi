from fastapi import APIRouter, HTTPException
from .. import verify_token, create_access_token
from .. import Token, RefreshRequest

router = APIRouter()

@router.post("/refresh_token", response_model = Token)
def refresh_token(data: RefreshRequest):
    payload = verify_token(data.refresh_token)
    if not payload:
        raise HTTPException(
            detail= "invalid or expired refresh token",
            status_code=401
        )
    
    new_access_token = create_access_token({
        "sub": payload["sub"],
        "is_superuser": payload["is_superuser"]
    })
    
    return {
        "access_token": new_access_token,
        "refresh_token": data.refresh_token,
        "token_type": "bearer"
    }