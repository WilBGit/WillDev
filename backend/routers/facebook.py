import os
import requests
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Client

FB_APP_ID = os.getenv("FB_APP_ID")
FB_APP_SECRET = os.getenv("FB_APP_SECRET")
FB_REDIRECT_URI = os.getenv("FB_REDIRECT_URI", "http://localhost:3000/facebook/connected")
FB_API_URL = "https://graph.facebook.com/v24.0"

router = APIRouter()
# ============================================================
# 1️⃣ Utility function — define this FIRST
# ============================================================
def get_or_create_client(db: Session, client_id: int = None):
    """
    Fetches a Client by ID if it exists, otherwise creates a new default one.
    Returns the client object and its (possibly new) ID.
    """
    if client_id:
        client = db.query(Client).filter(Client.id == client_id).first()
        if client:
            return client

    # Auto-create a new client if none found or ID not provided
    client = Client(
        name=f"Client_{client_id or 'auto'}",
        city="Unknown",
        industry="General"
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    print(f"🆕 Created new client with ID {client.id}")
    return client
@router.get("/facebook/login-url")
def facebook_login_url(client_id: int = None, db: Session = Depends(get_db)):
    FB_APP_ID = os.getenv("FB_APP_ID")
    FB_REDIRECT_URI = os.getenv("FB_REDIRECT_URI")
    FB_SCOPE = "pages_show_list,pages_manage_posts,pages_read_engagement,email"

    # ✅ Ensure a client exists or create one
    client = get_or_create_client(db, client_id)
    login_url = (
        f"https://www.facebook.com/v24.0/dialog/oauth"
        f"?client_id={FB_APP_ID}"
        f"&redirect_uri={FB_REDIRECT_URI}"
        f"&state={client.id}"
        f"&scope={FB_SCOPE}"
    )

    return {"url": login_url, "client_id": client.id}

@router.get("/facebook/callback")
def facebook_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handles Facebook redirect after login.
    Extracts both ?code=... and ?state=client_id.
    """
    # Extract query params manually
    params = dict(request.query_params)
    code = params.get("code")
    state = params.get("state")

    if not code:
        return {"error": "Missing 'code' parameter from Facebook"}

    # Facebook sends state as client_id
    client_id = int(state) if state and state.isdigit() else None

    # ✅ Ensure the client exists or create a new one
    client = get_or_create_client(db, client_id)

    # Then continue with the same logic below
    FB_APP_ID = os.getenv("FB_APP_ID")
    FB_APP_SECRET = os.getenv("FB_APP_SECRET")
    FB_REDIRECT_URI = os.getenv("FB_REDIRECT_URI")
    FB_API_URL = os.getenv("FB_API_URL", "https://graph.facebook.com/v24.0")

    # Exchange Facebook code for access token
    token_url = (
        f"{FB_API_URL}/oauth/access_token"
        f"?client_id={FB_APP_ID}"
        f"&redirect_uri={FB_REDIRECT_URI}"
        f"&client_secret={FB_APP_SECRET}"
        f"&code={code}"
    )

    r = requests.get(token_url)
    token_data = r.json()
    access_token = token_data.get("access_token")

    if not access_token:
        print("❌ Token exchange failed:", token_data)
        return {"error": "Token exchange failed", "details": token_data, "client_id": client.id}

    # Get managed Facebook pages
    pages_url = f"{FB_API_URL}/me/accounts?access_token={access_token}"
    pages_res = requests.get(pages_url).json()
    pages = pages_res.get("data", [])

    # Save pages to DB
    client.temp_facebook_pages = pages
    db.add(client)
    db.commit()
    db.refresh(client)

    print(f"✅ Saved {len(pages)} pages for client {client.id}")

    return {"client_id": client.id, "pages": pages}

@router.post("/facebook/select-page")
def select_page(data: dict, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == data["client_id"]).first()
    if not client:
        return {"error": "client_not_found"}

    client.facebook_page_id = data["page_id"]
    client.facebook_page_token = data["page_token"]
    db.commit()
    db.refresh(client)
    return {"status": "saved"}

@router.get("/facebook/pages")
def get_temp_pages(client_id: int, db: Session = Depends(get_db)):
    from backend.models import Client
    import requests, os, json

    FB_API_URL = os.getenv("FB_API_URL", "https://graph.facebook.com/v24.0")

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        return {"error": f"Client with ID {client_id} not found"}

    # ✅ If we already have pages saved temporarily
    if client.temp_facebook_pages:
        return {"client_id": client.id, "pages": client.temp_facebook_pages}

    # ✅ Try to refetch if a user/page token exists
    if not client.facebook_page_token:
        print(f"⚠️ No access token found for client {client.id}")
        return {"client_id": client.id, "pages": []}

    try:
        print(f"🔄 Fetching live pages from Facebook for client {client.id}")
        res = requests.get(
            f"{FB_API_URL}/me/accounts?access_token={client.facebook_page_token}"
        )
        pages_json = res.json()

        print("📘 Live pages response:", json.dumps(pages_json, indent=2))

        pages = pages_json.get("data", [])
        client.temp_facebook_pages = pages
        db.add(client)
        db.commit()
        db.refresh(client)

        return {"client_id": client.id, "pages": pages}

    except Exception as e:
        print(f"❌ Error fetching live pages: {e}")
        return {"error": str(e), "client_id": client.id, "pages": []}
@router.post("/facebook/save-page")
def save_facebook_page(data: dict, db: Session = Depends(get_db)):
    client_id = int(data["client_id"])
    page_id = data["page_id"]
    page_token = data["page_token"]

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        return {"error": f"Client {client_id} not found"}

    client.facebook_page_id = page_id
    client.facebook_page_token = page_token
    client.temp_facebook_pages = None  # optional cleanup

    db.add(client)  # ✅ ensure update is staged
    db.commit()     # ✅ ensure write happens

    return {"ok": True}