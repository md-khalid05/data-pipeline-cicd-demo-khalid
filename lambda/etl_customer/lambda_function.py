import csv
import io
import json
import os

import boto3

from transform import row_to_item

S3_BUCKET = os.environ.get("S3_BUCKET", "testingrawdata")
S3_KEY = os.environ.get("S3_KEY", "data-etl-test1/customer.csv")
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "etl-test")


def lambda_handler(event, context):
    print("Lambda started")

    s3 = boto3.client("s3")
    print("S3 client created")

    dynamodb = boto3.resource("dynamodb")
    print("DynamoDB resource created")

    table = dynamodb.Table(DYNAMODB_TABLE)
    print(f"Using table: {DYNAMODB_TABLE}")

    bucket = event.get("bucket", S3_BUCKET)
    key = event.get("key", S3_KEY)

    print(f"Bucket={bucket}")
    print(f"Key={key}")

    response = s3.get_object(Bucket=bucket, Key=key)
    print("S3 object downloaded")

    body = response["Body"].read().decode("utf-8")
    print("File read")

    reader = csv.DictReader(io.StringIO(body))

    records_written = 0

    with table.batch_writer() as batch:
        print("Batch writer opened")

        for row in reader:
            batch.put_item(Item=row_to_item(row, key))
            records_written += 1

    print(f"Wrote {records_written} records")

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "records_written": records_written
            }
        ),
    }
