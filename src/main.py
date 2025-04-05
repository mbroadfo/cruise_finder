import logging
import time
import boto3
from trip_parser import TripParser
from save_trips import save_to_json
from aws_secrets import inject_env_from_secrets
inject_env_from_secrets("cruise-finder-secrets")

def invalidate_cloudfront_cache(distribution_id: str, paths: list[str]) -> None:
    client = boto3.client('cloudfront')
    response = client.create_invalidation(
        DistributionId=distribution_id,
        InvalidationBatch={
            'Paths': {
                'Quantity': len(paths),
                'Items': paths
            },
            'CallerReference': str(time.time())  # Unique per request
        }
    )
    print("✅ CloudFront invalidation submitted:", response['Invalidation']['Id'])
    
def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    parser = TripParser()
    trips = parser.fetch_trips(limit=50)

    if trips:
        save_to_json(trips)  # Save JSON first
        invalidate_cloudfront_cache("E22G95LIEIJY6O", ["/trip_list.json"])  # Invalidate after S3 push
    else:
        logging.info("No trips with available departures found. Skipping CSV export.")

if __name__ == "__main__":
    main()
