from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from app.core.security import sign_session_token, verify_passcode_input
from app.schemas.common import ok_response

router = APIRouter()


class UnlockRequest(BaseModel):
    passcode: str


@router.post("/unlock")
async def unlock_workspace(body: UnlockRequest, response: Response):
    if not verify_passcode_input(body.passcode):
        raise HTTPException(status_code=401, detail="Invalid studio passcode.")
    token = sign_session_token("owner")
    response.set_cookie(
        key="studio_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=30 * 24 * 3600,
    )
    return ok_response({"authenticated": True})
