from datetime import datetime, timedelta
import logging
import os
import time
import json
import jwt
from functools import wraps
from flask import Flask, g, jsonify, request, send_from_directory, redirect
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import (
    db,
    User,
    Transaction,
    TransactionSplit,
    SettlementSession,
    HistoricalSettlement,
    Trip,
    BalanceList,
    BalanceListMember,
    generate_invite_code,
)
from ocr import get_ocr_service
from bank_parser import BankParser
from category_classifier import classify_transaction, get_all_categories
from sqlalchemy import func
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Request logging to console
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)
if not app.logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    app.logger.addHandler(h)


@app.before_request
def before_request():
    g.request_start = time.perf_counter()


_frontend_origin = (os.getenv("FRONTEND_URL") or "").strip()
if _frontend_origin:
    CORS(app, origins=[_frontend_origin])
else:
    CORS(app)

_secret = os.getenv("SECRET_KEY", "dev-secret-key-12345")
if os.getenv("FLASK_ENV") == "production" or os.getenv("DATABASE_URL"):
    if _secret == "dev-secret-key-12345" or len(_secret) < 32:
        raise RuntimeError("Set a strong SECRET_KEY (≥32 chars) in production.")
app.config["SECRET_KEY"] = _secret
UPLOAD_FOLDER = "uploads"
AVATAR_FOLDER = "avatars"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AVATAR_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["AVATAR_FOLDER"] = AVATAR_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

# Database Configuration
# DATABASE_URL from .env (Supabase Transaction Mode on port 6543)
database_url = os.getenv("DATABASE_URL")

# Handle potential missing colon in protocol and asyncpg driver if present
if database_url:
    if database_url.startswith("postgresql//"):
        database_url = database_url.replace("postgresql//", "postgresql://", 1)
    if "asyncpg" in database_url:
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

db.init_app(app)
migrate = Migrate(app, db)

# Rate limiter: only active when RATELIMIT_STORAGE_URI is configured (e.g. Redis).
# Without it, in-memory storage would spam warnings on multi-worker/restart deploys.
_ratelimit_storage = os.getenv("RATELIMIT_STORAGE_URI")
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=None,
    storage_uri=_ratelimit_storage or "memory://",
    enabled=bool(_ratelimit_storage),
)


@app.after_request
def after_request(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Request log
    elapsed = (time.perf_counter() - getattr(g, "request_start", time.perf_counter())) * 1000
    app.logger.info(
        "%s %s %s %.0fms",
        request.method,
        request.path,
        response.status_code,
        elapsed,
    )
    return response


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Preflight OPTIONS never sends Authorization; must return 2xx so CORS passes
        if request.method == "OPTIONS":
            return "", 204
        token = None
        if "Authorization" in request.headers:
            ah = request.headers["Authorization"]
            if ah.startswith("Bearer "):
                token = ah.split(" ")[1]
        if not token:
            return jsonify({"message": "Missing token"}), 401
        try:
            data = jwt.decode(
                token, app.config["SECRET_KEY"], algorithms=["HS256"]
            )
            user = db.session.get(User, data.get("user_id"))
            if not user:
                return jsonify({"message": "Invalid token"}), 401
        except Exception:
            return jsonify({"message": "Invalid token"}), 401
        return f(user, *args, **kwargs)

    return decorated


@app.route("/")
@limiter.exempt
def health():
    """Minimal health check: no DB, no limiter. Used by Render and clients."""
    return jsonify({"status": "ok"})


# @app.route("/init-db")
# @limiter.exempt
# def init_db():
#     """Seed demo data (BalanceList, users, trip, transactions). Dev only; does not touch schema (migrations own that)."""
#     if os.getenv("DATABASE_URL") and os.getenv("FLASK_ENV") == "production":
#         return jsonify({"error": "init-db disabled in production (set FLASK_ENV or unset DATABASE_URL for dev)"}), 403
#     try:
#         pw = generate_password_hash("wbw2026")
#         # Get or create users: Arjan, Fardau, Demo (all login with wbw2026)
#         m1 = User.query.filter_by(email="arjan@example.com").first()
#         if not m1:
#             m1 = User(name="Arjan", email="arjan@example.com", avatar_url="https://gravatar.com/avatar/ec8da171a095998421d4b15519c3ed42?s=400&d=robohash&r=x", is_group_member=True, password_hash=pw)
#             db.session.add(m1)
#         m2 = User.query.filter_by(email="fardau@example.com").first()
#         if not m2:
#             m2 = User(name="Fardau", email="fardau@example.com", avatar_url="https://gravatar.com/avatar/578d464ecbe91a131cafc9dcfe6323a7?s=400&d=robohash&r=x", is_group_member=True, password_hash=pw)
#             db.session.add(m2)
#         m3 = User.query.filter_by(email="demo@example.com").first()
#         if not m3:
#             m3 = User(name="Demo", email="demo@example.com", avatar_url="https://robohash.org/9699d97bfad1d597dc44a043286474e0?set=set4&bgset=&size=400x400", is_group_member=True, password_hash=pw)
#             db.session.add(m3)
#         db.session.flush()

#         # One balance list with members (so "Mijn balansen" has something)
#         bl = BalanceList.query.filter_by(name="Demo Groep").first()
#         if not bl:
#             bl = BalanceList(name="Demo Groep", currency="EUR", created_by_id=m1.id)
#             db.session.add(bl)
#             db.session.flush()
#             for u, role in [(m1, "owner"), (m2, "member"), (m3, "member")]:
#                 db.session.add(BalanceListMember(balance_list_id=bl.id, user_id=u.id, role=role))
#         db.session.flush()

#         today = datetime.utcnow().date()
#         yesterday = today - timedelta(days=1)
#         last_week = today - timedelta(days=7)
#         last_month = today - timedelta(days=30)

#         # Trip for the balance list
#         trip = Trip.query.filter_by(name="Weekendje Ardennen", balance_list_id=bl.id).first()
#         if not trip:
#             trip = Trip(name="Weekendje Ardennen", description="Weekend weg", balance_list_id=bl.id, is_active=True)
#             db.session.add(trip)
#             db.session.flush()

#         sess = SettlementSession.query.filter_by(description="Weekendje Ardennen", balance_list_id=bl.id).first()
#         if not sess:
#             sess = SettlementSession(date=datetime.utcnow() - timedelta(days=15), description="Weekendje Ardennen", balance_list_id=bl.id, trip_id=trip.id)
#             db.session.add(sess)
#             db.session.flush()

#             t_old = Transaction(description="Huur Huisje", amount=450.0, date=last_month, payer_id=m1.id, settlement_session_id=sess.id, balance_list_id=bl.id, trip_id=trip.id, type="EXPENSE")
#             db.session.add(t_old)
#             db.session.flush()
#             for u in [m1, m2, m3]:
#                 db.session.add(TransactionSplit(transaction_id=t_old.id, user_id=u.id, weight=1))
#             db.session.add_all([
#                 HistoricalSettlement(settlement_session_id=sess.id, from_user_id=m2.id, to_user_id=m1.id, amount=150.0),
#                 HistoricalSettlement(settlement_session_id=sess.id, from_user_id=m3.id, to_user_id=m1.id, amount=150.0),
#             ])

#         # Unsaved transactions (only if not already seeded)
#         if not Transaction.query.filter_by(balance_list_id=bl.id, description="Lunch bij Loetje").first():
#             t1 = Transaction(description="Lunch bij Loetje", amount=65.50, date=today, payer_id=m1.id, type="EXPENSE", balance_list_id=bl.id, trip_id=trip.id)
#             db.session.add(t1)
#             db.session.flush()
#             for u in [m1, m2, m3]:
#                 db.session.add(TransactionSplit(transaction_id=t1.id, user_id=u.id, weight=1))
#             t2 = Transaction(description="Boodschappen AH", amount=42.10, date=yesterday, payer_id=m2.id, type="EXPENSE", balance_list_id=bl.id)
#             db.session.add(t2)
#             db.session.flush()
#             for u in [m1, m2]:
#                 db.session.add(TransactionSplit(transaction_id=t2.id, user_id=u.id, weight=1))
#             t3 = Transaction(description="Benzine", amount=85.00, date=last_week, payer_id=m3.id, type="EXPENSE", balance_list_id=bl.id)
#             db.session.add(t3)
#             db.session.flush()
#             db.session.add(TransactionSplit(transaction_id=t3.id, user_id=m1.id, weight=2))
#             db.session.add(TransactionSplit(transaction_id=t3.id, user_id=m3.id, weight=1))

#         db.session.commit()
#         return jsonify({
#             "status": "success",
#             "balance_list_id": bl.id,
#             "message": "Seed data added. Log in with arjan@example.com / wbw2026 and open Demo Groep.",
#         })
#     except Exception as e:
#         db.session.rollback()
#         app.logger.exception("init-db failed")
#         return jsonify({"error": str(e)}), 500


@app.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    auth = request.get_json(silent=True) or {}
    username = (auth.get("username") or "").strip()
    password = auth.get("password")
    if not username or not password:
        return jsonify({"message": "Missing"}), 400
    u_lower = username.lower()
    user = User.query.filter(
        (func.lower(User.name) == u_lower) | (func.lower(User.email) == u_lower)
    ).first()
    if (
        not user
        or not user.password_hash
        or not check_password_hash(user.password_hash, password)
    ):
        return jsonify({"message": "Invalid"}), 401
    
    # Check email verification (skip for first login - when email_verified is None/False and no activation_token)
    # Users who registered but never activated need to verify their email for subsequent logins
    if user.activation_token and not user.email_verified:
        return jsonify({
            "message": "Email not verified",
            "requires_activation": True,
            "email": user.email
        }), 403
    
    tk = jwt.encode(
        {"user_id": user.id, "exp": datetime.utcnow() + timedelta(hours=24)},
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    return jsonify(
        {
            "token": tk,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "email_verified": user.email_verified,
            },
        }
    )


@app.route("/auth/register-from-invite", methods=["POST"])
@limiter.limit("5 per minute")
def register_from_invite():
    """Register a new account via invite code (invite-only signup)."""
    data = request.get_json(silent=True) or {}
    invite_code = data.get("invite_code", "").strip()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    
    if not invite_code:
        return jsonify({"error": "Invite code is required"}), 400
    if not name or len(name) < 2:
        return jsonify({"error": "Name is required (min 2 characters)"}), 400
    if not email or "@" not in email:
        return jsonify({"error": "Valid email is required"}), 400
    if not password or len(password) < 6:
        return jsonify({"error": "Password is required (min 6 characters)"}), 400
    
    # Verify invite code
    bl = BalanceList.query.filter_by(invite_code=invite_code).first()
    if not bl:
        return jsonify({"error": "Invalid invite code"}), 404
    
    # Check if email already exists
    existing = User.query.filter(func.lower(User.email) == email).first()
    if existing:
        return jsonify({"error": "Email already registered"}), 409
    
    try:
        # Create user
        user = User()
        user.name = name
        user.email = email
        user.password_hash = generate_password_hash(password)
        user.is_group_member = True
        user.email_verified = False
        user.generate_activation_token()
        db.session.add(user)
        db.session.flush()
        
        # Auto-join the balance list
        member = BalanceListMember()
        member.balance_list_id = bl.id
        member.user_id = user.id
        member.role = "member"
        db.session.add(member)
        db.session.commit()
        
        # Generate token for immediate login (first login allowed without activation)
        tk = jwt.encode(
            {"user_id": user.id, "exp": datetime.utcnow() + timedelta(hours=24)},
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        
        # TODO: Send activation email with user.activation_token
        # For now, log the activation URL
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        activation_url = f"{frontend_url}/activate?token={user.activation_token}"
        app.logger.info(f"Activation URL for {email}: {activation_url}")
        
        return jsonify({
            "status": "success",
            "message": "Account created. Check your email to activate for future logins.",
            "token": tk,
            "user": user.to_dict(),
            "balance_list": bl.to_dict(),
            "activation_url": activation_url if os.getenv("FLASK_ENV") != "production" else None
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app.logger.exception("register-from-invite failed")
        return jsonify({"error": str(e)}), 500


@app.route("/auth/activate", methods=["POST"])
@limiter.limit("10 per minute")
def activate_account():
    """Activate account by setting password and verifying email."""
    data = request.get_json(silent=True) or {}
    token = data.get("token", "").strip()
    new_password = data.get("password", "")
    
    if not token:
        return jsonify({"error": "Activation token is required"}), 400
    
    user = User.query.filter_by(activation_token=token).first()
    if not user:
        return jsonify({"error": "Invalid activation token"}), 404
    
    if not user.verify_activation_token(token):
        return jsonify({"error": "Activation token expired"}), 410
    
    try:
        # If password provided, update it
        if new_password:
            if len(new_password) < 6:
                return jsonify({"error": "Password must be at least 6 characters"}), 400
            user.password_hash = generate_password_hash(new_password)
        
        # Mark email as verified and clear token
        user.email_verified = True
        user.activation_token = None
        user.activation_token_expires = None
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Account activated successfully",
            "user": user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.exception("activate failed")
        return jsonify({"error": str(e)}), 500


@app.route("/auth/resend-activation", methods=["POST"])
@limiter.limit("3 per minute")
def resend_activation():
    """Resend activation email."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    user = User.query.filter(func.lower(User.email) == email).first()
    if not user:
        # Don't reveal if email exists
        return jsonify({"status": "success", "message": "If the email exists, an activation link was sent."})
    
    if user.email_verified:
        return jsonify({"error": "Account already activated"}), 400
    
    try:
        user.generate_activation_token()
        db.session.commit()
        
        # TODO: Send activation email
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        activation_url = f"{frontend_url}/activate?token={user.activation_token}"
        app.logger.info(f"Activation URL for {email}: {activation_url}")
        
        return jsonify({
            "status": "success",
            "message": "Activation email sent",
            "activation_url": activation_url if os.getenv("FLASK_ENV") != "production" else None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/auth/google", methods=["GET"])
@limiter.exempt
def google_auth():
    """Initiate Google OAuth flow."""
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not google_client_id:
        return jsonify({"error": "Google OAuth not configured"}), 503
    
    invite_code = request.args.get("invite_code", "")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", f"{request.host_url.rstrip('/')}/auth/google/callback")
    
    # Build state with invite_code if provided
    state_data = {"invite_code": invite_code} if invite_code else {}
    state = jwt.encode(state_data, app.config["SECRET_KEY"], algorithm="HS256")
    
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={google_client_id}&"
        f"redirect_uri={redirect_uri}&"
        "response_type=code&"
        "scope=openid%20email%20profile&"
        "prompt=consent&"  # Altijd consent/accountkeuze tonen na uitloggen
        f"state={state}"
    )
    
    return jsonify({"auth_url": auth_url})


@app.route("/auth/google/callback", methods=["GET", "POST"])
@limiter.exempt
def google_callback():
    """Handle Google OAuth callback."""
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    if not google_client_id or not google_client_secret:
        return jsonify({"error": "Google OAuth not configured"}), 503
    
    code = request.args.get("code") or (request.json or {}).get("code")
    state = request.args.get("state") or (request.json or {}).get("state")
    
    if not code:
        return _google_callback_error("Missing authorization code", 400)
    
    # Decode state to get invite_code
    invite_code = None
    if state:
        try:
            state_data = jwt.decode(state, app.config["SECRET_KEY"], algorithms=["HS256"])
            invite_code = state_data.get("invite_code")
        except Exception:
            pass
    
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", f"{request.host_url.rstrip('/')}/auth/google/callback")
    
    try:
        # Exchange code for tokens
        import requests as http_requests
        token_response = http_requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": google_client_id,
                "client_secret": google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        if not token_response.ok:
            try:
                err_body = token_response.json()
                msg = err_body.get("error_description") or err_body.get("error") or "Failed to exchange code for token"
            except Exception:
                msg = token_response.text or "Failed to exchange code for token"
            app.logger.warning("Google token exchange failed: %s %s", token_response.status_code, msg)
            return _google_callback_error("Failed to exchange code for token", 400, detail=msg)
        
        tokens = token_response.json()
        id_token = tokens.get("id_token")
        
        if not id_token:
            return _google_callback_error("No ID token received", 400)
        
        # Decode ID token to get user info (without verification for simplicity)
        # In production, should verify with Google's public keys
        import base64
        payload = id_token.split(".")[1]
        # Add padding if needed
        payload += "=" * (4 - len(payload) % 4)
        user_info = json.loads(base64.urlsafe_b64decode(payload))
        
        google_id = user_info.get("sub")
        email = user_info.get("email", "").lower()
        name = user_info.get("name", email.split("@")[0])
        picture = user_info.get("picture")
        
        if not google_id or not email:
            return _google_callback_error("Invalid user info from Google", 400)
        
        # Find or create user
        user = User.query.filter(
            (User.oauth_provider == "google") & (User.oauth_id == google_id)
        ).first()
        
        if not user:
            # Check if email exists (link accounts)
            user = User.query.filter(func.lower(User.email) == email).first()
            if user:
                # Link existing account to Google
                user.oauth_provider = "google"
                user.oauth_id = google_id
                user.email_verified = True
            else:
                # No existing account — auto-create from Google profile
                user = User()
                user.name = name
                user.email = email
                user.avatar_url = picture
                user.oauth_provider = "google"
                user.oauth_id = google_id
                user.is_group_member = True
                user.email_verified = True  # Google emails are pre-verified
                db.session.add(user)
                db.session.flush()

                # If invite_code provided, also auto-join the balance list
                if invite_code:
                    bl = BalanceList.query.filter_by(invite_code=invite_code).first()
                    if bl:
                        member = BalanceListMember()
                        member.balance_list_id = bl.id
                        member.user_id = user.id
                        member.role = "member"
                        db.session.add(member)
        
        # Update avatar if changed
        if picture and user.avatar_url != picture:
            user.avatar_url = picture
        
        db.session.commit()
        
        # Generate JWT
        tk = jwt.encode(
            {"user_id": user.id, "exp": datetime.utcnow() + timedelta(hours=24)},
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )

        # Browser GET (Google redirected here directly) → redirect to frontend with token + user.
        # The frontend picks up ?google_token=... and ?google_user=... and calls store.login() directly.
        frontend_url = os.getenv("FRONTEND_URL", "").rstrip("/")
        if request.method == "GET" and frontend_url:
            import base64 as _b64
            from urllib.parse import urlencode as _urlencode
            user_b64 = _b64.urlsafe_b64encode(json.dumps(user.to_dict()).encode()).decode()
            qs = _urlencode({"google_token": tk, "google_user": user_b64})
            resp = redirect(f"{frontend_url}/?{qs}", code=302)
            resp.headers["Access-Control-Allow-Origin"] = frontend_url
            return resp

        return jsonify({
            "status": "success",
            "token": tk,
            "user": user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.exception("google callback failed")
        return _google_callback_error(str(e), 500)


def _google_callback_error(message: str, status: int, *, detail: str = None, needs_invite: bool = False):
    """Return error for Google callback. If browser GET, redirect to frontend with error param."""
    payload = {"error": message}
    if detail:
        payload["detail"] = detail
    if needs_invite:
        payload["needs_invite"] = True
    frontend_url = os.getenv("FRONTEND_URL", "").rstrip("/")
    if request.method == "GET" and frontend_url:
        from urllib.parse import urlencode
        params = {"google_error": "needs_invite" if needs_invite else "error", "google_message": message}
        resp = redirect(f"{frontend_url}/?{urlencode(params)}", code=302)
        # CORS: fetch() that gets a redirect needs Access-Control-Allow-Origin on the 302 response
        resp.headers["Access-Control-Allow-Origin"] = frontend_url
        return resp
    return jsonify(payload), status


@app.route("/auth/me", methods=["GET"])
@token_required
def auth_me(current_user):
    """Return the authenticated user's profile."""
    return jsonify(current_user.to_dict())


@app.route("/users", methods=["GET"])
@token_required
def get_users(current_user):
    balance_list_id = request.args.get("balance_list_id", type=int)
    
    if balance_list_id:
        # Return only members of this balance list
        members = BalanceListMember.query.filter_by(balance_list_id=balance_list_id).all()
        users = [m.user for m in members if m.user]
    else:
        # Return all users (fallback for backward compatibility)
        users = User.query.all()
    
    return jsonify(
        [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "avatar_url": u.avatar_url,
                "is_group_member": u.is_group_member,
            }
            for u in users
        ]
    )


@app.route("/users/profile", methods=["PUT"])
@token_required
def update_profile(current_user):
    d = request.json
    if "avatar_url" in d:
        current_user.avatar_url = d["avatar_url"]
    if "name" in d:
        current_user.name = d["name"]
    if "email" in d:
        current_user.email = d["email"]
    db.session.commit()
    return jsonify(
        {
            "status": "success",
            "user": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email,
                "avatar_url": current_user.avatar_url,
            },
        }
    )


@app.route("/users/avatar", methods=["POST"])
@token_required
def upload_avatar(current_user):
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"error": "No file"}), 400
    fn = f"user_{current_user.id}_{secure_filename(f.filename)}"
    f.save(os.path.join(app.config["AVATAR_FOLDER"], fn))
    current_user.avatar_url = f"{request.host_url.rstrip('/')}/static/{fn}"
    db.session.commit()
    return jsonify(
        {
            "status": "success",
            "avatar_url": current_user.avatar_url,
            "user": {
                "id": current_user.id,
                "name": current_user.name,
                "avatar_url": current_user.avatar_url,
            },
        }
    )


# ===== BALANCE LISTS ENDPOINTS =====


def _get_balance_list_stats(balance_list, current_user):
    """Calculate stats for a balance list including user's balance."""
    txs = Transaction.query.filter_by(
        balance_list_id=balance_list.id,
        settlement_session_id=None
    ).filter(Transaction.deleted_at.is_(None)).all()
    
    total_amount = sum(t.amount for t in txs)
    
    # Calculate current user's balance within this list
    member_ids = [m.user_id for m in balance_list.members]
    bals = {uid: 0.0 for uid in member_ids}
    
    for t in txs:
        amt = t.amount
        tp = t.type or "EXPENSE"
        if t.payer_id in bals:
            if tp in ["EXPENSE", "TRANSFER"]:
                bals[t.payer_id] += amt
            else:
                bals[t.payer_id] -= amt
        tw = sum(s.weight for s in t.splits if s.user_id in member_ids)
        if tw > 0:
            ppw = amt / tw
            for s in t.splits:
                if s.user_id in bals:
                    if tp in ["EXPENSE", "TRANSFER"]:
                        bals[s.user_id] -= ppw * s.weight
                    else:
                        bals[s.user_id] += ppw * s.weight
    
    my_balance = bals.get(current_user.id, 0.0)
    
    return {
        "total_transactions": len(txs),
        "total_amount": round(total_amount, 2),
        "my_balance": round(my_balance, 2),
    }


@app.route("/balance-lists", methods=["GET"])
@token_required
def get_balance_lists(current_user):
    """Get all balance lists for the current user."""
    memberships = BalanceListMember.query.filter_by(user_id=current_user.id).all()
    result = []
    for m in memberships:
        bl = m.balance_list
        stats = _get_balance_list_stats(bl, current_user)
        data = bl.to_dict()
        data.update(stats)
        data["my_role"] = m.role
        result.append(data)
    return jsonify(result)


@app.route("/balance-lists", methods=["POST"])
@token_required
def create_balance_list(current_user):
    """Create a new balance list."""
    d = request.json or {}
    name = d.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400
    
    currency = d.get("currency", "EUR").upper()[:3]
    
    try:
        bl = BalanceList()
        bl.name = name
        bl.currency = currency
        bl.created_by_id = current_user.id
        db.session.add(bl)
        db.session.flush()
        
        # Add creator as owner
        member = BalanceListMember()
        member.balance_list_id = bl.id
        member.user_id = current_user.id
        member.role = "owner"
        db.session.add(member)
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "balance_list": bl.to_dict(include_members=True)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/balance-lists/<int:bl_id>", methods=["GET"])
@token_required
def get_balance_list(current_user, bl_id):
    """Get a specific balance list."""
    bl = db.session.get(BalanceList, bl_id)
    if not bl:
        return jsonify({"error": "Not found"}), 404
    
    # Check membership
    membership = BalanceListMember.query.filter_by(
        balance_list_id=bl_id, user_id=current_user.id
    ).first()
    if not membership:
        return jsonify({"error": "Access denied"}), 403
    
    data = bl.to_dict(include_members=True)
    stats = _get_balance_list_stats(bl, current_user)
    data.update(stats)
    data["my_role"] = membership.role
    return jsonify(data)


@app.route("/balance-lists/<int:bl_id>", methods=["PUT"])
@token_required
def update_balance_list(current_user, bl_id):
    """Update a balance list (name, currency)."""
    bl = db.session.get(BalanceList, bl_id)
    if not bl:
        return jsonify({"error": "Not found"}), 404
    
    membership = BalanceListMember.query.filter_by(
        balance_list_id=bl_id, user_id=current_user.id
    ).first()
    if not membership or membership.role not in ["owner", "admin"]:
        return jsonify({"error": "Only owner or admin can edit"}), 403
    
    d = request.json or {}
    try:
        if "name" in d:
            bl.name = d["name"].strip()
        if "currency" in d:
            bl.currency = d["currency"].upper()[:3]
        db.session.commit()
        return jsonify({"status": "success", "balance_list": bl.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/balance-lists/<int:bl_id>", methods=["DELETE"])
@token_required
def delete_balance_list(current_user, bl_id):
    """Delete a balance list (owner only)."""
    bl = db.session.get(BalanceList, bl_id)
    if not bl:
        return jsonify({"error": "Not found"}), 404
    
    membership = BalanceListMember.query.filter_by(
        balance_list_id=bl_id, user_id=current_user.id
    ).first()
    if not membership or membership.role != "owner":
        return jsonify({"error": "Only owner can delete"}), 403
    
    try:
        db.session.delete(bl)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/balance-lists/<int:bl_id>/members", methods=["GET"])
@token_required
def get_balance_list_members(current_user, bl_id):
    """Get all members of a balance list, including their net unsettled balance."""
    bl = db.session.get(BalanceList, bl_id)
    if not bl:
        return jsonify({"error": "Not found"}), 404

    membership = BalanceListMember.query.filter_by(
        balance_list_id=bl_id, user_id=current_user.id
    ).first()
    if not membership:
        return jsonify({"error": "Access denied"}), 403

    # Compute per-member unsettled balance
    txs = Transaction.query.filter_by(
        balance_list_id=bl_id,
        settlement_session_id=None,
    ).filter(Transaction.deleted_at.is_(None)).all()

    member_ids = [m.user_id for m in bl.members]
    bals = {uid: 0.0 for uid in member_ids}
    for t in txs:
        tp = t.type or "EXPENSE"
        sign = 1 if tp in ["EXPENSE", "TRANSFER"] else -1
        if t.payer_id in bals:
            bals[t.payer_id] += sign * t.amount
        tw = sum(s.weight for s in t.splits if s.user_id in member_ids)
        if tw > 0:
            ppw = t.amount / tw
            for s in t.splits:
                if s.user_id in bals:
                    bals[s.user_id] -= sign * ppw * s.weight

    result = []
    for m in bl.members:
        d = m.to_dict()
        d["balance"] = round(bals.get(m.user_id, 0.0), 2)
        result.append(d)
    return jsonify(result)


@app.route("/balance-lists/<int:bl_id>/members", methods=["POST"])
@token_required
def add_balance_list_member(current_user, bl_id):
    """Add a member to a balance list by user_id."""
    bl = db.session.get(BalanceList, bl_id)
    if not bl:
        return jsonify({"error": "Not found"}), 404
    
    membership = BalanceListMember.query.filter_by(
        balance_list_id=bl_id, user_id=current_user.id
    ).first()
    if not membership or membership.role not in ["owner", "admin"]:
        return jsonify({"error": "Only owner or admin can add members"}), 403
    
    d = request.json or {}
    user_id = d.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    existing = BalanceListMember.query.filter_by(
        balance_list_id=bl_id, user_id=user_id
    ).first()
    if existing:
        return jsonify({"error": "User is already a member"}), 400
    
    try:
        member = BalanceListMember()
        member.balance_list_id = bl_id
        member.user_id = user_id
        member.role = d.get("role", "member")
        db.session.add(member)
        db.session.commit()
        return jsonify({"status": "success", "member": member.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/balance-lists/<int:bl_id>/members/<int:user_id>", methods=["DELETE"])
@token_required
def remove_balance_list_member(current_user, bl_id, user_id):
    """Remove a member from a balance list.
    
    Only allowed when the target member's net balance is exactly zero
    (all unsettled transactions have been accounted for). Owner/admin can
    remove others; any member can remove themselves.
    """
    bl = db.session.get(BalanceList, bl_id)
    if not bl:
        return jsonify({"error": "Not found"}), 404

    membership = BalanceListMember.query.filter_by(
        balance_list_id=bl_id, user_id=current_user.id
    ).first()

    is_self = current_user.id == user_id
    is_admin = membership and membership.role in ["owner", "admin"]
    if not is_self and not is_admin:
        return jsonify({"error": "Permission denied"}), 403

    target = BalanceListMember.query.filter_by(
        balance_list_id=bl_id, user_id=user_id
    ).first()
    if not target:
        return jsonify({"error": "Member not found"}), 404

    # Owner cannot be removed by others (only by themselves, i.e. leaving)
    if target.role == "owner" and not is_self:
        return jsonify({"error": "Cannot remove the owner"}), 403

    # Compute the target user's net unsettled balance in this list
    txs = Transaction.query.filter_by(
        balance_list_id=bl_id,
        settlement_session_id=None,
    ).filter(Transaction.deleted_at.is_(None)).all()

    member_ids = [m.user_id for m in bl.members]
    bals = {uid: 0.0 for uid in member_ids}
    for t in txs:
        tp = t.type or "EXPENSE"
        sign = 1 if tp in ["EXPENSE", "TRANSFER"] else -1
        if t.payer_id in bals:
            bals[t.payer_id] += sign * t.amount
        tw = sum(s.weight for s in t.splits if s.user_id in member_ids)
        if tw > 0:
            ppw = t.amount / tw
            for s in t.splits:
                if s.user_id in bals:
                    bals[s.user_id] -= sign * ppw * s.weight

    net_balance = round(bals.get(user_id, 0.0), 2)
    if net_balance != 0.0:
        direction = "nog te ontvangen" if net_balance > 0 else "nog te betalen"
        return jsonify({
            "error": f"Lid heeft nog een openstaand saldo van €{abs(net_balance):.2f} ({direction}). "
                     "Vereffening vereist voor verwijdering.",
            "balance": net_balance,
        }), 409

    try:
        db.session.delete(target)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/balance-lists/<int:bl_id>/invite-code", methods=["GET"])
@token_required
def get_invite_code(current_user, bl_id):
    """Get the invite code for a balance list."""
    bl = db.session.get(BalanceList, bl_id)
    if not bl:
        return jsonify({"error": "Not found"}), 404
    
    membership = BalanceListMember.query.filter_by(
        balance_list_id=bl_id, user_id=current_user.id
    ).first()
    if not membership:
        return jsonify({"error": "Access denied"}), 403
    
    return jsonify({
        "invite_code": bl.invite_code,
        "balance_list_id": bl.id,
        "balance_list_name": bl.name
    })


@app.route("/balance-lists/<int:bl_id>/invite-code/regenerate", methods=["POST"])
@token_required
def regenerate_invite_code(current_user, bl_id):
    """Regenerate the invite code for a balance list."""
    bl = db.session.get(BalanceList, bl_id)
    if not bl:
        return jsonify({"error": "Not found"}), 404
    
    membership = BalanceListMember.query.filter_by(
        balance_list_id=bl_id, user_id=current_user.id
    ).first()
    if not membership or membership.role not in ["owner", "admin"]:
        return jsonify({"error": "Only owner or admin can regenerate invite code"}), 403
    
    try:
        bl.invite_code = generate_invite_code()
        db.session.commit()
        return jsonify({
            "status": "success",
            "invite_code": bl.invite_code
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/balance-lists/join/<invite_code>", methods=["POST"])
@token_required
def join_balance_list(current_user, invite_code):
    """Join a balance list via invite code."""
    bl = BalanceList.query.filter_by(invite_code=invite_code).first()
    if not bl:
        return jsonify({"error": "Invalid invite code"}), 404
    
    existing = BalanceListMember.query.filter_by(
        balance_list_id=bl.id, user_id=current_user.id
    ).first()
    if existing:
        return jsonify({
            "status": "already_member",
            "balance_list": bl.to_dict()
        })
    
    try:
        member = BalanceListMember()
        member.balance_list_id = bl.id
        member.user_id = current_user.id
        member.role = "member"
        db.session.add(member)
        db.session.commit()
        return jsonify({
            "status": "success",
            "balance_list": bl.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/balance-lists/lookup/<invite_code>", methods=["GET"])
@token_required
def lookup_balance_list(current_user, invite_code):
    """Look up a balance list by invite code (for preview before joining)."""
    bl = BalanceList.query.filter_by(invite_code=invite_code).first()
    if not bl:
        return jsonify({"error": "Invalid invite code"}), 404
    
    is_member = BalanceListMember.query.filter_by(
        balance_list_id=bl.id, user_id=current_user.id
    ).first() is not None
    
    return jsonify({
        "id": bl.id,
        "name": bl.name,
        "currency": bl.currency,
        "member_count": len(bl.members),
        "is_member": is_member
    })


@app.route("/balance-lists/public-preview/<invite_code>", methods=["GET"])
@limiter.exempt
def public_preview_balance_list(invite_code):
    """Public endpoint: preview a balance list by invite code (no auth required)."""
    bl = BalanceList.query.filter_by(invite_code=invite_code).first()
    if not bl:
        return jsonify({"error": "Invalid invite code"}), 404
    
    return jsonify({
        "id": bl.id,
        "name": bl.name,
        "currency": bl.currency,
        "member_count": len(bl.members),
        "created_by_name": bl.created_by.name if bl.created_by else None,
    })


@app.route("/static/<path:filename>")
def serve_static(filename):
    if os.path.exists(os.path.join(app.config["AVATAR_FOLDER"], filename)):
        return send_from_directory(app.config["AVATAR_FOLDER"], filename)
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


def _tx_not_deleted(query):
    """Helper to filter out soft-deleted transactions"""
    return query.filter(Transaction.deleted_at.is_(None))


@app.route("/balances", methods=["GET"])
@token_required
def get_balances(current_user):
    activity_id = request.args.get("activity_id", type=int)
    balance_list_id = request.args.get("balance_list_id", type=int)
    
    if balance_list_id:
        # Get only members of this balance list
        members = BalanceListMember.query.filter_by(balance_list_id=balance_list_id).all()
        users = [m.user for m in members if m.user]
    else:
        users = User.query.all()
    
    query = Transaction.query.filter_by(settlement_session_id=None)
    query = _tx_not_deleted(query)
    if balance_list_id is not None:
        query = query.filter_by(balance_list_id=balance_list_id)
    if activity_id is not None:
        query = query.filter_by(trip_id=activity_id)
    txs = query.all()
    bals = {u.id: 0.0 for u in users}
    for t in txs:
        amt = t.amount
        tp = t.type or "EXPENSE"
        if t.payer_id in bals:
            if tp in ["EXPENSE", "TRANSFER"]:
                bals[t.payer_id] += amt
            else:
                bals[t.payer_id] -= amt
        tw = sum(s.weight for s in t.splits)
        if tw > 0:
            ppw = amt / tw
            for s in t.splits:
                if s.user_id in bals:
                    if tp in ["EXPENSE", "TRANSFER"]:
                        bals[s.user_id] -= ppw * s.weight
                    else:
                        bals[s.user_id] += ppw * s.weight
    return jsonify(
        [{"user_id": uid, "balance": round(bal, 2)} for uid, bal in bals.items()]
    )


@app.route("/transactions", methods=["GET"])
@token_required
def get_transactions(current_user):
    activity_id = request.args.get("activity_id", type=int)
    balance_list_id = request.args.get("balance_list_id", type=int)
    category = request.args.get("category", type=str)
    deleted = request.args.get("deleted", "false").lower() == "true"
    query = Transaction.query.filter_by(settlement_session_id=None)
    if deleted:
        query = query.filter(Transaction.deleted_at.isnot(None))
    else:
        query = _tx_not_deleted(query)
    if balance_list_id is not None:
        query = query.filter_by(balance_list_id=balance_list_id)
    if activity_id is not None:
        query = query.filter_by(trip_id=activity_id)
    if category:
        query = query.filter_by(category=category)
    txs = query.order_by(Transaction.date.desc(), Transaction.time.desc()).all()
    if deleted:
        txs = sorted(
            txs,
            key=lambda t: (t.deleted_at or datetime.min, t.date, t.time or ""),
            reverse=True,
        )
    return jsonify(
        [
            {
                "id": t.id,
                "date": t.date.isoformat(),
                "time": t.time or "00:00",
                "description": t.description,
                "amount": t.amount,
                "type": t.type or "EXPENSE",
                "category": t.category or "overig",
                "payer_id": t.payer_id,
                "activity_id": t.trip_id,
                "balance_list_id": t.balance_list_id,
                "deleted_at": t.deleted_at.isoformat() if t.deleted_at else None,
                "splits": [
                    {"user_id": s.user_id, "weight": s.weight} for s in t.splits
                ],
            }
            for t in txs
        ]
    )


@app.route("/transactions", methods=["POST"])
@token_required
def add_transaction(current_user):
    d = request.json
    try:
        t = Transaction()
        t.description = d["description"]
        t.amount = float(d["amount"])
        t.type = d.get("type", "EXPENSE")
        t.date = (
            datetime.strptime(d["date"], "%Y-%m-%d").date()
            if isinstance(d.get("date"), str)
            else datetime.utcnow().date()
        )
        t.time = d.get("time", datetime.utcnow().strftime("%H:%M"))
        t.payer_id = d["payer_id"]
        # Auto-classify if category not provided
        t.category = d.get("category") or classify_transaction(d["description"])
        if "activity_id" in d and d["activity_id"]:
            t.trip_id = d["activity_id"]
        if "balance_list_id" in d and d["balance_list_id"]:
            t.balance_list_id = d["balance_list_id"]
        db.session.add(t)
        db.session.flush()
        for s_data in d["splits"]:
            split = TransactionSplit()
            split.transaction_id = t.id
            split.user_id = s_data["user_id"]
            split.weight = s_data.get("weight", 1)
            db.session.add(split)
        db.session.commit()
        return jsonify({"status": "success", "id": t.id, "category": t.category})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/transactions/<int:tx_id>", methods=["PUT"])
@token_required
def update_transaction(current_user, tx_id):
    d = request.json
    try:
        t = db.session.get(Transaction, tx_id)
        if not t:
            return jsonify({"error": "Not found"}), 404
        t.description = d["description"]
        t.amount = float(d["amount"])
        t.type = d.get("type", "EXPENSE")
        if isinstance(d.get("date"), str):
            t.date = datetime.strptime(d["date"], "%Y-%m-%d").date()
        if isinstance(d.get("time"), str):
            t.time = d["time"]
        t.payer_id = d["payer_id"]
        if "category" in d:
            t.category = d["category"] or classify_transaction(d["description"])
        if "activity_id" in d:
            t.trip_id = d["activity_id"] if d["activity_id"] else None
        if "balance_list_id" in d:
            t.balance_list_id = d["balance_list_id"] if d["balance_list_id"] else None
        TransactionSplit.query.filter_by(transaction_id=tx_id).delete()
        for s_data in d["splits"]:
            split = TransactionSplit()
            split.transaction_id = tx_id
            split.user_id = s_data["user_id"]
            split.weight = s_data.get("weight", 1)
            db.session.add(split)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/transactions/bulk", methods=["PATCH"])
@token_required
def bulk_update_transactions(current_user):
    d = request.json
    if not d or "transaction_ids" not in d:
        return jsonify({"error": "transaction_ids required"}), 400
    ids = d["transaction_ids"]
    if not ids:
        return jsonify({"updated": 0, "skipped": 0})
    has_activity = "activity_id" in d
    has_splits = "splits" in d and d["splits"] is not None
    if not has_activity and not has_splits:
        return jsonify({"error": "activity_id or splits required"}), 400
    activity_id = d.get("activity_id") if has_activity else None
    splits = d.get("splits") if has_splits else None
    try:
        query = Transaction.query.filter(
            Transaction.id.in_(ids),
            Transaction.settlement_session_id.is_(None),
            Transaction.deleted_at.is_(None),
        )
        txs = query.all()
        updated = 0
        for t in txs:
            if has_activity:
                t.trip_id = activity_id if activity_id else None
            if splits:
                TransactionSplit.query.filter_by(transaction_id=t.id).delete()
                for s_data in splits:
                    split = TransactionSplit(
                        transaction_id=t.id,
                        user_id=s_data["user_id"],
                        weight=s_data.get("weight", 1),
                    )
                    db.session.add(split)
            updated += 1
        db.session.commit()
        return jsonify(
            {"status": "success", "updated": updated, "skipped": len(ids) - updated}
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/transactions/<int:tx_id>", methods=["DELETE"])
@token_required
def delete_transaction(current_user, tx_id):
    try:
        t = db.session.get(Transaction, tx_id)
        if not t:
            return jsonify({"status": "success"})
        if t.settlement_session_id is not None:
            return jsonify(
                {"error": "Afgerekende transactie kan niet verwijderd worden"}
            ), 403
        t.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"status": "success", "soft": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/transactions/<int:tx_id>/restore", methods=["POST"])
@token_required
def restore_transaction(current_user, tx_id):
    try:
        t = db.session.get(Transaction, tx_id)
        if not t:
            return jsonify({"error": "Not found"}), 404
        if t.deleted_at is None:
            return jsonify({"error": "Niet verwijderd"}), 400
        t.deleted_at = None
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/transactions/<int:tx_id>/permanent", methods=["DELETE"])
@token_required
def delete_transaction_permanent(current_user, tx_id):
    try:
        t = db.session.get(Transaction, tx_id)
        if not t:
            return jsonify({"error": "Not found"}), 404
        if t.deleted_at is None:
            return jsonify(
                {"error": "Alleen uit prullenbak definitief verwijderen"}
            ), 400
        db.session.delete(t)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/settlements/suggest", methods=["GET"])
@token_required
def suggest_settlement(current_user):
    activity_id = request.args.get("activity_id", type=int)
    balance_list_id = request.args.get("balance_list_id", type=int)
    
    if balance_list_id:
        members = BalanceListMember.query.filter_by(balance_list_id=balance_list_id).all()
        users = [m.user for m in members if m.user]
    else:
        users = User.query.all()
    
    query = Transaction.query.filter_by(settlement_session_id=None)
    query = _tx_not_deleted(query)
    if balance_list_id is not None:
        query = query.filter_by(balance_list_id=balance_list_id)
    if activity_id is not None:
        query = query.filter_by(trip_id=activity_id)
    txs = query.all()
    bals = {u.id: 0.0 for u in users}
    for t in txs:
        amt = t.amount
        tp = t.type or "EXPENSE"
        if t.payer_id in bals:
            if tp in ["EXPENSE", "TRANSFER"]:
                bals[t.payer_id] += amt
            else:
                bals[t.payer_id] -= amt
        tw = sum(s.weight for s in t.splits)
        if tw > 0:
            ppw = amt / tw
            for s in t.splits:
                if s.user_id in bals:
                    if tp in ["EXPENSE", "TRANSFER"]:
                        bals[s.user_id] -= ppw * s.weight
                    else:
                        bals[s.user_id] += ppw * s.weight
    u_map = {u.id: u.name for u in users}
    dbtr = [[uid, abs(bal)] for uid, bal in bals.items() if bal < -0.01]
    crtr = [[uid, bal] for uid, bal in bals.items() if bal > 0.01]
    dbtr.sort(key=lambda x: x[1], reverse=True)
    crtr.sort(key=lambda x: x[1], reverse=True)
    res, d_i, c_i = [], 0, 0
    while d_i < len(dbtr) and c_i < len(crtr):
        amt = min(dbtr[d_i][1], crtr[c_i][1])
        res.append(
            {
                "from_user_id": dbtr[d_i][0],
                "from_user": u_map[dbtr[d_i][0]],
                "to_user_id": crtr[c_i][0],
                "to_user": u_map[crtr[c_i][0]],
                "amount": round(amt, 2),
            }
        )
        dbtr[d_i][1] -= amt
        crtr[c_i][1] -= amt
        if dbtr[d_i][1] < 0.01:
            d_i += 1
        if crtr[c_i][1] < 0.01:
            c_i += 1
    return jsonify(res)


@app.route("/settlements/commit", methods=["POST"])
@token_required
def commit_settlement(current_user):
    try:
        d = request.json or {}
        activity_id = d.get("activity_id") or request.args.get("activity_id", type=int)
        balance_list_id = d.get("balance_list_id") or request.args.get("balance_list_id", type=int)
        
        query = Transaction.query.filter_by(settlement_session_id=None)
        query = _tx_not_deleted(query)
        if balance_list_id is not None:
            query = query.filter_by(balance_list_id=balance_list_id)
        if activity_id is not None:
            query = query.filter_by(trip_id=activity_id)
        unsettled = query.all()
        if not unsettled:
            return jsonify({"message": "Nothing to settle"}), 400
        
        if balance_list_id:
            members = BalanceListMember.query.filter_by(balance_list_id=balance_list_id).all()
            users = [m.user for m in members if m.user]
        else:
            users = User.query.all()
        
        bals = {u.id: 0.0 for u in users}
        for t in unsettled:
            amt = t.amount
            tp = t.type or "EXPENSE"
            if t.payer_id in bals:
                if tp in ["EXPENSE", "TRANSFER"]:
                    bals[t.payer_id] += amt
                else:
                    bals[t.payer_id] -= amt
            tw = sum(s.weight for s in t.splits)
            if tw > 0:
                ppw = amt / tw
                for s in t.splits:
                    if s.user_id in bals:
                        if tp in ["EXPENSE", "TRANSFER"]:
                            bals[s.user_id] -= ppw * s.weight
                        else:
                            bals[s.user_id] += ppw * s.weight
        u_map = {u.id: u.name for u in users}
        dbtr = [[uid, abs(bal)] for uid, bal in bals.items() if bal < -0.01]
        crtr = [[uid, bal] for uid, bal in bals.items() if bal > 0.01]
        dbtr.sort(key=lambda x: x[1], reverse=True)
        crtr.sort(key=lambda x: x[1], reverse=True)
        suggestions = []
        d_i, c_i = 0, 0
        while d_i < len(dbtr) and c_i < len(crtr):
            amt = min(dbtr[d_i][1], crtr[c_i][1])
            suggestions.append(
                {
                    "from_user_id": dbtr[d_i][0],
                    "from_user": u_map[dbtr[d_i][0]],
                    "to_user_id": crtr[c_i][0],
                    "to_user": u_map[crtr[c_i][0]],
                    "amount": round(amt, 2),
                }
            )
            dbtr[d_i][1] -= amt
            crtr[c_i][1] -= amt
            if dbtr[d_i][1] < 0.01:
                d_i += 1
            if crtr[c_i][1] < 0.01:
                c_i += 1
        if not suggestions:
            return jsonify({"message": "Nothing to settle"}), 400
        sess = SettlementSession()
        sess.description = f"Verrekening door {current_user.name}" + (
            f" - {Trip.query.get(activity_id).name}" if activity_id else ""
        )
        if activity_id:
            sess.trip_id = activity_id
        if balance_list_id:
            sess.balance_list_id = balance_list_id
        db.session.add(sess)
        db.session.flush()
        for t in unsettled:
            t.settlement_session_id = sess.id
        for s in suggestions:
            hs = HistoricalSettlement()
            hs.settlement_session_id = sess.id
            hs.from_user_id = s["from_user_id"]
            hs.to_user_id = s["to_user_id"]
            hs.amount = s["amount"]
            db.session.add(hs)
        db.session.commit()
        return jsonify(
            {"status": "success", "session_id": sess.id, "activity_id": activity_id, "balance_list_id": balance_list_id}
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/settlements/history", methods=["GET"])
@token_required
def get_settlement_history(current_user):
    deleted = request.args.get("deleted", "false").lower() == "true"
    balance_list_id = request.args.get("balance_list_id", type=int)
    
    query = SettlementSession.query
    if deleted:
        query = query.filter(SettlementSession.deleted_at.isnot(None))
    else:
        query = query.filter(SettlementSession.deleted_at.is_(None))
    if balance_list_id is not None:
        query = query.filter_by(balance_list_id=balance_list_id)
    sessions = query.order_by(SettlementSession.date.desc()).all()
    res = []
    for s in sessions:
        total = sum(h.amount for h in s.results)
        txs = sorted(s.transactions, key=lambda t: (t.date, t.time or ""))
        transactions = [
            {
                "id": t.id,
                "date": t.date.isoformat(),
                "time": t.time,
                "amount": round(t.amount, 2),
                "description": t.description,
                "payer": t.payer.name if t.payer else None,
            }
            for t in txs
        ]
        res.append(
            {
                "id": s.id,
                "date": s.date.isoformat(),
                "description": s.description,
                "total_amount": round(total, 2),
                "balance_list_id": s.balance_list_id,
                "deleted_at": s.deleted_at.isoformat() if s.deleted_at else None,
                "results": [
                    {
                        "from_user": h.from_user.name,
                        "to_user": h.to_user.name,
                        "amount": h.amount,
                    }
                    for h in s.results
                ],
                "transactions": transactions,
            }
        )
    return jsonify(res)


@app.route("/settlements/<int:session_id>", methods=["DELETE"])
@token_required
def delete_settlement(current_user, session_id):
    """Soft delete a settlement (move to trash) and restore transactions"""
    try:
        s = db.session.get(SettlementSession, session_id)
        if not s:
            return jsonify({"error": "Not found"}), 404
        s.deleted_at = datetime.utcnow()
        # Restore all transactions by clearing their settlement_session_id
        restored_count = 0
        for t in s.transactions:
            t.settlement_session_id = None
            restored_count += 1
        db.session.commit()
        return jsonify(
            {
                "status": "success",
                "soft": True,
                "restored_transactions": restored_count,
                "message": f"Verrekening ongedaan gemaakt. {restored_count} transactie(s) hersteld.",
            }
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/settlements/<int:session_id>/restore", methods=["POST"])
@token_required
def restore_settlement(current_user, session_id):
    """Restore a soft-deleted settlement from trash (re-settle transactions)"""
    try:
        s = db.session.get(SettlementSession, session_id)
        if not s:
            return jsonify({"error": "Not found"}), 404
        if s.deleted_at is None:
            return jsonify({"error": "Niet verwijderd"}), 400
        s.deleted_at = None
        # Note: transactions stay unsettled when settlement is restored from trash
        # This allows reviewing the settlement before committing again
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/settlements/<int:session_id>/permanent", methods=["DELETE"])
@token_required
def delete_settlement_permanent(current_user, session_id):
    try:
        s = db.session.get(SettlementSession, session_id)
        if not s:
            return jsonify({"error": "Not found"}), 404
        if s.deleted_at is None:
            return jsonify(
                {"error": "Alleen uit prullenbak definitief verwijderen"}
            ), 400
        # Transactions should already be unsettled from soft delete
        db.session.delete(s)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/categories", methods=["GET"])
@token_required
def get_categories(current_user):
    return jsonify(get_all_categories())


@app.route("/import/bank", methods=["POST"])
@token_required
def import_bank(current_user):
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    bank_type = request.form.get("bank_type", "ing")
    content = request.files["file"].read().decode("utf-8")
    try:
        data = (
            BankParser.parse_ing_csv(content)
            if bank_type == "ing"
            else BankParser.parse_abn_csv(content)
        )
        return jsonify({"status": "success", "transactions": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/ocr/process", methods=["POST"])
@token_required
def process_receipt(current_user):
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"error": "No file"}), 400
    fn = secure_filename(f.filename)
    fp = os.path.join(app.config["UPLOAD_FOLDER"], fn)
    f.save(fp)
    try:
        svc = get_ocr_service()
        if svc is None:
            return jsonify({"error": "OCR not available (easyocr not installed)"}), 503
        return jsonify(
            {"status": "success", "data": svc.process_receipt(fp)}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== ACTIVITIES (TRIPS) ENDPOINTS =====


@app.route("/activities", methods=["GET"])
@token_required
def get_activities(current_user):
    include_archived = request.args.get("include_archived", "false").lower() == "true"
    balance_list_id = request.args.get("balance_list_id", type=int)
    
    query = Trip.query
    if not include_archived:
        query = query.filter((Trip.is_active == True) | (Trip.archived_at == None))
    if balance_list_id is not None:
        query = query.filter_by(balance_list_id=balance_list_id)
    trips = query.order_by(Trip.created_at.desc()).all()
    res = []
    for t in trips:
        txs = _tx_not_deleted(
            Transaction.query.filter_by(trip_id=t.id, settlement_session_id=None)
        ).all()
        total = sum(tx.amount for tx in txs)
        res.append(
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "start_date": t.start_date.isoformat() if t.start_date else None,
                "end_date": t.end_date.isoformat() if t.end_date else None,
                "color": t.color,
                "icon": t.icon,
                "is_active": t.is_active,
                "archived_at": t.archived_at.isoformat() if t.archived_at else None,
                "balance_list_id": t.balance_list_id,
                "transaction_count": len(txs),
                "total_amount": round(total, 2),
            }
        )
    return jsonify(res)


@app.route("/activities", methods=["POST"])
@token_required
def create_activity(current_user):
    d = request.json
    try:
        t = Trip()
        t.name = d["name"]
        t.description = d.get("description")
        if d.get("start_date"):
            t.start_date = datetime.strptime(d["start_date"], "%Y-%m-%d").date()
        if d.get("end_date"):
            t.end_date = datetime.strptime(d["end_date"], "%Y-%m-%d").date()
        t.color = d.get("color", "#E30613")
        t.icon = d.get("icon", "📋")
        t.is_active = True
        if d.get("balance_list_id"):
            t.balance_list_id = d["balance_list_id"]
        db.session.add(t)
        db.session.commit()
        return jsonify(
            {
                "status": "success",
                "id": t.id,
                "activity": {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "start_date": t.start_date.isoformat() if t.start_date else None,
                    "end_date": t.end_date.isoformat() if t.end_date else None,
                    "color": t.color,
                    "icon": t.icon,
                    "is_active": t.is_active,
                    "balance_list_id": t.balance_list_id,
                },
            }
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/activities/<int:activity_id>", methods=["GET"])
@token_required
def get_activity(current_user, activity_id):
    t = db.session.get(Trip, activity_id)
    if not t:
        return jsonify({"error": "Not found"}), 404
    txs = _tx_not_deleted(Transaction.query.filter_by(trip_id=activity_id)).all()
    return jsonify(
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "start_date": t.start_date.isoformat() if t.start_date else None,
            "end_date": t.end_date.isoformat() if t.end_date else None,
            "color": t.color,
            "icon": t.icon,
            "is_active": t.is_active,
            "archived_at": t.archived_at.isoformat() if t.archived_at else None,
            "transaction_count": len(txs),
        }
    )


@app.route("/activities/<int:activity_id>", methods=["PUT"])
@token_required
def update_activity(current_user, activity_id):
    t = db.session.get(Trip, activity_id)
    if not t:
        return jsonify({"error": "Not found"}), 404
    d = request.json
    try:
        if "name" in d:
            t.name = d["name"]
        if "description" in d:
            t.description = d["description"]
        if "start_date" in d:
            t.start_date = (
                datetime.strptime(d["start_date"], "%Y-%m-%d").date()
                if d["start_date"]
                else None
            )
        if "end_date" in d:
            t.end_date = (
                datetime.strptime(d["end_date"], "%Y-%m-%d").date()
                if d["end_date"]
                else None
            )
        if "color" in d:
            t.color = d["color"]
        if "icon" in d:
            t.icon = d["icon"]
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/activities/<int:activity_id>", methods=["DELETE"])
@token_required
def archive_activity(current_user, activity_id):
    t = db.session.get(Trip, activity_id)
    if not t:
        return jsonify({"error": "Not found"}), 404
    try:
        t.is_active = False
        t.archived_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/activities/<int:activity_id>/transactions", methods=["GET"])
@token_required
def get_activity_transactions(current_user, activity_id):
    include_settled = request.args.get("include_settled", "false").lower() == "true"
    query = Transaction.query.filter_by(trip_id=activity_id)
    query = _tx_not_deleted(query)
    if not include_settled:
        query = query.filter_by(settlement_session_id=None)
    txs = query.order_by(Transaction.date.desc(), Transaction.time.desc()).all()
    return jsonify(
        [
            {
                "id": t.id,
                "date": t.date.isoformat(),
                "time": t.time or "00:00",
                "description": t.description,
                "amount": t.amount,
                "type": t.type or "EXPENSE",
                "category": t.category or "overig",
                "payer_id": t.payer_id,
                "splits": [
                    {"user_id": s.user_id, "weight": s.weight} for s in t.splits
                ],
            }
            for t in txs
        ]
    )


@app.route("/activities/<int:activity_id>/balance", methods=["GET"])
@token_required
def get_activity_balance(current_user, activity_id):
    users = User.query.all()
    txs = _tx_not_deleted(
        Transaction.query.filter_by(trip_id=activity_id, settlement_session_id=None)
    ).all()
    bals = {u.id: 0.0 for u in users}
    for t in txs:
        amt = t.amount
        tp = t.type or "EXPENSE"
        if t.payer_id in bals:
            if tp in ["EXPENSE", "TRANSFER"]:
                bals[t.payer_id] += amt
            else:
                bals[t.payer_id] -= amt
        tw = sum(s.weight for s in t.splits)
        if tw > 0:
            ppw = amt / tw
            for s in t.splits:
                if s.user_id in bals:
                    if tp in ["EXPENSE", "TRANSFER"]:
                        bals[s.user_id] -= ppw * s.weight
                    else:
                        bals[s.user_id] += ppw * s.weight
    trip = db.session.get(Trip, activity_id)
    return jsonify(
        {
            "activity_id": activity_id,
            "activity_name": trip.name if trip else None,
            "balances": [
                {"user_id": uid, "balance": round(bal, 2)} for uid, bal in bals.items()
            ],
            "total_amount": round(sum(t.amount for t in txs), 2),
        }
    )


@app.route("/activities/<int:activity_id>/settlement/suggest", methods=["GET"])
@token_required
def suggest_activity_settlement(current_user, activity_id):
    # Temporarily set activity_id in request args
    original_args = request.args.copy()
    request.args = request.args.copy()
    request.args["activity_id"] = activity_id
    result = suggest_settlement(current_user)
    request.args = original_args
    return result


@app.route("/activities/<int:activity_id>/settlement/commit", methods=["POST"])
@token_required
def commit_activity_settlement(current_user, activity_id):
    d = request.json or {}
    d["activity_id"] = activity_id
    request.json = d
    return commit_settlement(current_user)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    app.run(debug=True, host="0.0.0.0", port=port)
