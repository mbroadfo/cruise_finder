import boto3
from botocore.exceptions import NoCredentialsError

S3_BUCKET = "mytripdata8675309"
FILE_KEY = "trip_list.json"

s3_client = boto3.client("s3")

try:
    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": FILE_KEY},
        ExpiresIn=3600  # 1 hour expiry
    )
    print(f"Presigned URL: {presigned_url}")
except NoCredentialsError:
    print("Error: No AWS credentials found.")
