import os
import requests
import secrets
import string
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)
from src.aws_secrets import inject_env_from_secrets

# Inject secrets from AWS Secrets Manager
inject_env_from_secrets("cruise-finder-secrets")

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
        "email_verified": True,
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

def find_user(email):
    """List all users in the Auth0 tenant."""
    token = get_m2m_token()
    url = f"https://{AUTH0_DOMAIN}/api/v2/users?q={email}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    users = resp.json()
    
    return users[0] if users else None
    
def list_users():
    """List all users in the Auth0 tenant."""
    token = get_m2m_token()
    url = f"https://{AUTH0_DOMAIN}/api/v2/users"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    users = []
    page = 0
    per_page = 50  # max allowed by Auth0 is 100

    while True:
        params = {
            "page": page,
            "per_page": per_page
        }

        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        batch = resp.json()

        if not batch:
            break  # No more users

        users.extend(batch)
        page += 1

    print(f"\n👥 Found {len(users)} users:\n")
    for user in users:
        print(f"- {user.get('email')} ({user.get('user_id')})")

def delete_user(user_id):
    """Delete a user from Auth0 by user ID."""
    token = get_m2m_token()
    url = f"https://{AUTH0_DOMAIN}/api/v2/users/{user_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    resp = requests.delete(url, headers=headers)
    if resp.status_code == 204:
        print(f"🗑️ User {user_id} deleted successfully.")
    else:
        print("❌ Failed to delete user:")
        print(resp.status_code, resp.text)
        resp.raise_for_status()
