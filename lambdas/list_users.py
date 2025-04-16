import json
import os
from admin.auth0_utils import list_users

def lambda_handler(event, context):
    try:
        users = list_users()

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
