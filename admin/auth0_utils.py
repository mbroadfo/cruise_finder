import os
import requests
import secrets
import string
from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_WEB_CLIENT_ID = os.getenv("AUTH0_WEB_CLIENT_ID")
AUTH0_CONNECTION = os.getenv("AUTH0_CONNECTION", "Username-Password-Authentication")
CLOUD_FRONT_URI = os.getenv("CLOUD_FRONT_URI")

def get_m2m_token():
    url = f"https://{AUTH0_DOMAIN}/oauth/token"
    payload = {
        "client_id": AUTH0_CLIENT_ID,
        "client_secret": AUTH0_CLIENT_SECRET,
        "audience": f"https://{AUTH0_DOMAIN}/api/v2/",
        "grant_type": "client_credentials",
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()["access_token"]

def generate_temp_password(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return ''.join(secrets.choice(chars) for _ in range(length))

def create_user(email, given_name, family_name, token):
    url = f"https://{AUTH0_DOMAIN}/api/v2/users"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "email": email,
        "given_name": given_name,
        "family_name": family_name,
        "connection": AUTH0_CONNECTION,
        "password": generate_temp_password()
    }
    resp = requests.post(url, json=payload, headers=headers)
    if not resp.ok:
        print("❌ Error response from Auth0:")
        print(resp.status_code, resp.text)
        resp.raise_for_status()
    return resp.json()

def send_password_reset_email(email, token=None):
    url = f"https://{AUTH0_DOMAIN}/dbconnections/change_password"
    payload = {
        "client_id": AUTH0_WEB_CLIENT_ID,
        "email": email,
        "connection": AUTH0_CONNECTION
    }
    headers = {
        "Content-Type": "application/json"
    }

    print("\n📦 Sending password reset email with:")
    print(f"🔗 Endpoint : {url}")
    print(f"📧 Email    : {email}")
    print(f"🔌 Client ID: {AUTH0_CLIENT_ID}")
    print(f"🔗 Connection: {AUTH0_CONNECTION}")

    resp = requests.post(url, json=payload, headers=headers)

    if not resp.ok:
        print("❌ Password reset request failed:")
        print(resp.status_code, resp.text)

    resp.raise_for_status()
    print("📬 Password reset email sent by Auth0!")
