from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
    base64url_to_bytes,
)
from webauthn.helpers.structs import (
    RegistrationCredential,
    AuthenticationCredential,
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    AuthenticatorAttachment,
)
from datetime import datetime
import json
from database import get_db
from models import User, UserSecurityKey
from auth.dependencies import get_current_user
from auth.jwt_handler import create_access_token

router = APIRouter()

# RP (Relying Party) Configuration
RP_ID = "localhost" # In production, this would be your domain
RP_NAME = "AeroGuard AI"
ORIGIN = "http://localhost:3000" # Frontend URL

# ────────────────────────────────────────────────────────
# REGISTRATION (Enrollment)
# ────────────────────────────────────────────────────────

@router.get("/register/options")
def get_registration_options(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generates options for the browser to create a new biometric credential."""
    # Check if user already has a key (optional: allow multiple keys)
    exclude_credentials = []
    for key in current_user.security_keys:
        exclude_credentials.append({
            "id": base64url_to_bytes(key.credential_id),
            "type": "public-key"
        })

    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=str(current_user.id).encode("utf-8"),
        user_name=current_user.email,
        user_display_name=current_user.full_name,
        attestation="none",
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=exclude_credentials,
    )

    # Store challenge in session or temporary cache (for demo, we'll return it)
    return json.loads(options_to_json(options))

@router.post("/register/verify")
def verify_registration(
    credential_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verifies the response from the browser and saves the public key."""
    try:
        # Note: In a real app, you must verify the challenge against the one stored in Step 1
        # For this prototype, we'll assume the client sends back a valid challenge
        verification = verify_registration_response(
            credential=credential_data,
            expected_challenge=base64url_to_bytes(credential_data["response"]["clientDataJSON"]), # This is a simplification
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            require_user_verification=True,
        )

        # Save to database
        new_key = UserSecurityKey(
            user_id=current_user.id,
            credential_id=verification.credential_id,
            public_key=verification.public_key.decode("utf-8") if isinstance(verification.public_key, bytes) else str(verification.public_key),
            sign_count=verification.sign_count,
            device_type="Biometric (Platform)",
        )
        db.add(new_key)
        db.commit()

        return {"status": "success", "message": "Biometric registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration verification failed: {str(e)}")

# ────────────────────────────────────────────────────────
# AUTHENTICATION (Login)
# ────────────────────────────────────────────────────────

@router.post("/login/options")
def get_login_options(email: str, db: Session = Depends(get_db)):
    """Generates options for the browser to sign a challenge."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.security_keys:
        raise HTTPException(status_code=404, detail="User not found or no biometric enrolled")

    allow_credentials = []
    for key in user.security_keys:
        allow_credentials.append({
            "id": base64url_to_bytes(key.credential_id),
            "type": "public-key"
        })

    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.REQUIRED,
    )

    return json.loads(options_to_json(options))

@router.post("/login/verify")
def verify_login(credential_data: dict, email: str, db: Session = Depends(get_db)):
    """Verifies the biometric signature and issues a JWT token."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
         raise HTTPException(status_code=404, detail="User not found")

    # Find the specific key used
    credential_id = credential_data["id"]
    db_key = db.query(UserSecurityKey).filter(UserSecurityKey.credential_id == credential_id).first()
    
    if not db_key:
        raise HTTPException(status_code=400, detail="Invalid security key")

    try:
        verification = verify_authentication_response(
            credential=credential_data,
            expected_challenge=b"temporary_challenge", # Simplified for demo
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            credential_public_key=db_key.public_key.encode("utf-8"),
            credential_current_sign_count=db_key.sign_count,
            require_user_verification=True,
        )

        # Update sign count
        db_key.sign_count = verification.new_sign_count
        db_key.last_used = datetime.utcnow() # Add this field if you want
        db.commit()

        # Issue JWT
        access_token = create_access_token(data={"sub": user.email})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")
