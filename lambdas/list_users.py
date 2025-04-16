import json
import os
from admin.auth0_utils import get_m2m_token, get_all_users

def lambda_handler(event, context):
    try:
        token = get_m2m_token()
        users = get_all_users(token)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(users)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }