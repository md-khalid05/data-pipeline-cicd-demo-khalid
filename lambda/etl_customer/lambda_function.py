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
    s3 = boto3.client("s3")
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(DYNAMODB_TABLE)

    bucket = event.get("bucket", S3_BUCKET)
    key = event.get("key", S3_KEY)

    response = s3.get_object(Bucket=bucket, Key=key)
    body = response["Body"].read().decode("utf-8")

    reader = csv.DictReader(io.StringIO(body))
    records_written = 0

    with table.batch_writer() as batch:
        for row in reader:
            batch.put_item(Item=row_to_item(row, key))
            records_written += 1

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "ETL completed successfully",
                "bucket": bucket,
                "key": key,
                "records_written": records_written,
                "table": DYNAMODB_TABLE,
            }
        ),
    }
