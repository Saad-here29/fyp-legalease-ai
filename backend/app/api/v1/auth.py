"""Authentication router — /auth/* endpoints.

Implements:
  POST /auth/register        — (alias /auth/signup) MX-validate + send OTP
  POST /auth/verify-email    — (alias /auth/verify-otp) confirm OTP, issue tokens
  POST /auth/resend-otp      — re-send the verification code
  POST /auth/login           — Algorithm 1 from Final Report § 4.1
  POST /auth/logout          — clear auth cookies
  POST /auth/refresh         — rotate access + refresh tokens
  GET  /auth/me              — current user
  POST /auth/forgot-password — email a reset code
  POST /auth/reset-password  — verify reset code + set new password

All token-issuing endpoints set httpOnly cookies; the response body keeps
the tokens too so Postman / mobile clients can still use them via Bearer.
"""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.cookies import (
    REFRESH_COOKIE,
    clear_auth_cookies,
    set_auth_cookies,
)
from app.core.exceptions import NotAuthenticated
from app.db.session import get_db
from app.middlewares.auth import CurrentUser
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshRequest,
    ResendOtpRequest,
    ResetPasswordRequest,
    SignupAcceptedResponse,
    SignupRequest,
    TokenPair,
    UserRead,
    VerifyOtpRequest,
)
from app.services.auth_service import AuthService

router = APIRouter()


# ===== Registration → OTP → verified login ================================


@router.post(
    "/register",
    response_model=SignupAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Validate email + create pending account + send OTP",
)
@router.post(
    "/signup",
    response_model=SignupAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Alias of /register for backward compatibility",
)
def register(
    payload: SignupRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    return AuthService(db, request).signup(payload)


@router.post(
    "/resend-otp",
    response_model=SignupAcceptedResponse,
    summary="Re-send the verification code",
)
def resend_otp(
    payload: ResendOtpRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    return AuthService(db, request).resend_otp(payload.email)


@router.post(
    "/verify-email",
    response_model=SignupAcceptedResponse,
    summary="Verify the OTP and activate the account. User is then asked to sign in.",
)
@router.post(
    "/verify-otp",
    response_model=SignupAcceptedResponse,
    summary="Alias of /verify-email",
)
def verify_email(
    payload: VerifyOtpRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    return AuthService(db, request).verify_otp(payload.email, payload.otp)


# ===== Login / refresh / logout ===========================================


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and issue JWT pair (UC-01)",
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    result = AuthService(db, request).login(
        email=payload.email, password=payload.password
    )
    set_auth_cookies(
        response,
        access_token=result.tokens.access_token,
        refresh_token=result.tokens.refresh_token,
    )
    return result


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Rotate the access + refresh token pair",
)
def refresh(
    payload: RefreshRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    # Prefer cookie; fall back to body for non-browser clients
    token = request.cookies.get(REFRESH_COOKIE) or payload.refresh_token
    if not token:
        raise NotAuthenticated("Missing refresh token.")
    new_pair = AuthService(db, request).refresh(token)
    set_auth_cookies(
        response,
        access_token=new_pair.access_token,
        refresh_token=new_pair.refresh_token,
    )
    return new_pair


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout — clear auth cookies",
)
def logout(
    user: CurrentUser,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    AuthService(db, request).audit("LOGOUT_OK", user_id=user.id)
    db.commit()
    clear_auth_cookies(response)
    return MessageResponse(message="Logged out successfully.")


# ===== Current user =======================================================


@router.get(
    "/me",
    response_model=UserRead,
    summary="Return the authenticated user's profile",
)
def me(user: CurrentUser):
    return user


# ===== Forgot / reset password ============================================


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Email a 6-digit password-reset code",
)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    result = AuthService(db, request).forgot_password(payload.email)
    return MessageResponse(message=result["message"])


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Verify the reset OTP and set a new password",
)
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    result = AuthService(db, request).reset_password(
        email=payload.email,
        otp=payload.otp,
        new_password=payload.new_password,
    )
    return MessageResponse(message=result["message"])
