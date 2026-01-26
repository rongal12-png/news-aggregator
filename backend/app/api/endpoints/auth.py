from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import secrets
import httpx

from app.db import get_db
from app.models import User, UserSession, Favorite, Story, StorySummary
from app.config import settings

router = APIRouter()
security = HTTPBearer(auto_error=False)

# Session settings
SESSION_EXPIRY_DAYS = 30

# OAuth URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

FACEBOOK_AUTH_URL = "https://www.facebook.com/v18.0/dialog/oauth"
FACEBOOK_TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
FACEBOOK_USERINFO_URL = "https://graph.facebook.com/me"


def hash_password(password: str) -> str:
    """Simple password hashing (in production, use bcrypt)."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == password_hash


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from session token."""
    if not credentials:
        return None

    token = credentials.credentials
    session = db.query(UserSession).filter(
        UserSession.token == token,
        UserSession.expires_at > datetime.now(timezone.utc)
    ).first()

    if not session:
        return None

    return session.user


async def require_auth(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """Require authentication - raises 401 if not logged in."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


# ============ AUTH ENDPOINTS ============

@router.post("/register")
async def register(
    email: str,
    password: str,
    name: Optional[str] = None,
    locale: str = "en",
    db: Session = Depends(get_db)
):
    """Register a new user with email/password."""
    # Check if email already exists
    existing = db.query(User).filter(User.email == email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Validate email format (basic)
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Invalid email format")

    # Validate password length
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    # Create user
    user = User(
        email=email.lower(),
        name=name,
        password_hash=hash_password(password),
        provider="email",
        locale=locale,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create session
    token = UserSession.generate_token()
    session = UserSession(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=SESSION_EXPIRY_DAYS)
    )
    db.add(session)
    db.commit()

    return {
        "message": "Registration successful",
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "locale": user.locale,
            "avatar_url": user.avatar_url
        }
    }


@router.post("/login")
async def login(
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    """Login with email/password."""
    user = db.query(User).filter(User.email == email.lower()).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.password_hash:
        raise HTTPException(status_code=401, detail="This account uses social login")

    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is disabled")

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)

    # Create session
    token = UserSession.generate_token()
    session = UserSession(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=SESSION_EXPIRY_DAYS)
    )
    db.add(session)
    db.commit()

    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "locale": user.locale,
            "avatar_url": user.avatar_url
        }
    }


@router.post("/logout")
async def logout(
    user: User = Depends(require_auth),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Logout and invalidate current session."""
    token = credentials.credentials
    db.query(UserSession).filter(UserSession.token == token).delete()
    db.commit()
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(user: User = Depends(require_auth)):
    """Get current user profile."""
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "locale": user.locale,
        "avatar_url": user.avatar_url,
        "is_admin": user.is_admin,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.put("/me")
async def update_me(
    name: Optional[str] = None,
    locale: Optional[str] = None,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    if name is not None:
        user.name = name
    if locale is not None:
        user.locale = locale

    db.commit()
    return {"message": "Profile updated"}


# ============ FAVORITES ENDPOINTS ============

@router.get("/favorites")
async def get_favorites(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get user's favorite stories."""
    favorites = db.query(Favorite).filter(
        Favorite.user_id == user.id
    ).order_by(Favorite.created_at.desc()).all()

    result = []
    for fav in favorites:
        story = db.query(Story).filter(Story.id == fav.story_id).first()
        if not story:
            continue

        summary = db.query(StorySummary).filter(
            StorySummary.story_id == story.id,
            StorySummary.language == user.locale
        ).first()

        # Fallback to English if no localized summary
        if not summary:
            summary = db.query(StorySummary).filter(
                StorySummary.story_id == story.id,
                StorySummary.language == "en"
            ).first()

        result.append({
            "story_id": story.id,
            "title": summary.title if summary else f"Story #{story.id}",
            "category": story.category,
            "published_at": story.published_at.isoformat() if story.published_at else None,
            "favorited_at": fav.created_at.isoformat() if fav.created_at else None
        })

    return {"favorites": result}


@router.post("/favorites/{story_id}")
async def add_favorite(
    story_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add a story to favorites."""
    # Check story exists
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Check if already favorited
    existing = db.query(Favorite).filter(
        Favorite.user_id == user.id,
        Favorite.story_id == story_id
    ).first()

    if existing:
        return {"message": "Already in favorites", "is_favorite": True}

    # Add favorite
    favorite = Favorite(user_id=user.id, story_id=story_id)
    db.add(favorite)
    db.commit()

    return {"message": "Added to favorites", "is_favorite": True}


@router.delete("/favorites/{story_id}")
async def remove_favorite(
    story_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Remove a story from favorites."""
    deleted = db.query(Favorite).filter(
        Favorite.user_id == user.id,
        Favorite.story_id == story_id
    ).delete()

    db.commit()

    if deleted:
        return {"message": "Removed from favorites", "is_favorite": False}
    return {"message": "Not in favorites", "is_favorite": False}


@router.get("/favorites/{story_id}/check")
async def check_favorite(
    story_id: int,
    user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a story is in user's favorites."""
    if not user:
        return {"is_favorite": False}

    exists = db.query(Favorite).filter(
        Favorite.user_id == user.id,
        Favorite.story_id == story_id
    ).first()

    return {"is_favorite": bool(exists)}


# ============ OAUTH ENDPOINTS ============

def create_session_for_user(user: User, db: Session) -> str:
    """Create a session token for a user."""
    user.last_login_at = datetime.now(timezone.utc)
    token = UserSession.generate_token()
    session = UserSession(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=SESSION_EXPIRY_DAYS)
    )
    db.add(session)
    db.commit()
    return token


def get_or_create_oauth_user(
    email: str,
    name: str,
    provider: str,
    provider_id: str,
    avatar_url: Optional[str],
    db: Session
) -> User:
    """Get existing user or create new one from OAuth data."""
    # Try to find existing user by provider_id
    user = db.query(User).filter(
        User.provider == provider,
        User.provider_id == provider_id
    ).first()

    if user:
        # Update user info
        user.name = name or user.name
        user.avatar_url = avatar_url or user.avatar_url
        db.commit()
        return user

    # Try to find by email
    user = db.query(User).filter(User.email == email.lower()).first()
    if user:
        # Link existing account to OAuth provider
        user.provider = provider
        user.provider_id = provider_id
        user.avatar_url = avatar_url or user.avatar_url
        db.commit()
        return user

    # Create new user
    user = User(
        email=email.lower(),
        name=name,
        provider=provider,
        provider_id=provider_id,
        avatar_url=avatar_url,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============ GOOGLE OAUTH ============

@router.get("/google")
async def google_login():
    """Redirect to Google OAuth login."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")

    redirect_uri = f"{settings.FRONTEND_URL}/auth/callback/google"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account"
    }
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return {"auth_url": f"{GOOGLE_AUTH_URL}?{query_string}"}


@router.post("/google/callback")
async def google_callback(
    code: str,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=501, detail="Google OAuth not configured")

    redirect_uri = f"{settings.FRONTEND_URL}/auth/callback/google"

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            }
        )

        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Google token")

        tokens = token_response.json()
        access_token = tokens.get("access_token")

        # Get user info
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Google user info")

        userinfo = userinfo_response.json()

    # Create or get user
    user = get_or_create_oauth_user(
        email=userinfo.get("email"),
        name=userinfo.get("name"),
        provider="google",
        provider_id=userinfo.get("id"),
        avatar_url=userinfo.get("picture"),
        db=db
    )

    # Create session
    token = create_session_for_user(user, db)

    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "locale": user.locale,
            "avatar_url": user.avatar_url
        }
    }


# ============ FACEBOOK OAUTH ============

@router.get("/facebook")
async def facebook_login():
    """Redirect to Facebook OAuth login."""
    if not settings.FACEBOOK_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Facebook OAuth not configured")

    redirect_uri = f"{settings.FRONTEND_URL}/auth/callback/facebook"
    params = {
        "client_id": settings.FACEBOOK_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": "email,public_profile",
        "response_type": "code"
    }
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return {"auth_url": f"{FACEBOOK_AUTH_URL}?{query_string}"}


@router.post("/facebook/callback")
async def facebook_callback(
    code: str,
    db: Session = Depends(get_db)
):
    """Handle Facebook OAuth callback."""
    if not settings.FACEBOOK_CLIENT_ID or not settings.FACEBOOK_CLIENT_SECRET:
        raise HTTPException(status_code=501, detail="Facebook OAuth not configured")

    redirect_uri = f"{settings.FRONTEND_URL}/auth/callback/facebook"

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.get(
            FACEBOOK_TOKEN_URL,
            params={
                "client_id": settings.FACEBOOK_CLIENT_ID,
                "client_secret": settings.FACEBOOK_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_uri
            }
        )

        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Facebook token")

        tokens = token_response.json()
        access_token = tokens.get("access_token")

        # Get user info
        userinfo_response = await client.get(
            FACEBOOK_USERINFO_URL,
            params={
                "fields": "id,name,email,picture.type(large)",
                "access_token": access_token
            }
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Facebook user info")

        userinfo = userinfo_response.json()

    # Get avatar URL from nested structure
    avatar_url = None
    if "picture" in userinfo and "data" in userinfo["picture"]:
        avatar_url = userinfo["picture"]["data"].get("url")

    # Create or get user
    user = get_or_create_oauth_user(
        email=userinfo.get("email", f"{userinfo.get('id')}@facebook.com"),
        name=userinfo.get("name"),
        provider="facebook",
        provider_id=userinfo.get("id"),
        avatar_url=avatar_url,
        db=db
    )

    # Create session
    token = create_session_for_user(user, db)

    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "locale": user.locale,
            "avatar_url": user.avatar_url
        }
    }
