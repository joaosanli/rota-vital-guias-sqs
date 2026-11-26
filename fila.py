import boto3


def cliente():
    return boto3.client("sqs", endpoint_url="http://localhost:9324",
                        region_name="us-east-1", aws_access_key_id="x",
                        aws_secret_access_key="x")
