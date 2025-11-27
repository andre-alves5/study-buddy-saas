from fastapi.testclient import TestClient
from unittest.mock import patch
import main
import jwt
import importlib
import pytest
import os
from moto import mock_aws
import boto3

client = TestClient(main.app)


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def aws(aws_credentials):
    with mock_aws():
        yield {
            "s3": boto3.client("s3", region_name="us-east-1"),
            "sqs": boto3.client("sqs", region_name="us-east-1"),
            "dynamodb": boto3.resource("dynamodb", region_name="us-east-1"),
        }


@patch("jwt.decode")
def test_generate_upload_url_success(mock_jwt_decode, aws, monkeypatch):
    # Set environment variables
    monkeypatch.setenv("S3_BUCKET", "test-bucket")
    monkeypatch.setenv("SQS_QUEUE_URL", "test-queue")
    monkeypatch.setenv("DYNAMODB_TABLE", "test-table")
    importlib.reload(main)

    # Setup mock resources
    s3 = aws["s3"]
    sqs = aws["sqs"]
    dynamodb = aws["dynamodb"]

    s3.create_bucket(Bucket="test-bucket")
    sqs.create_queue(QueueName="test-queue")
    dynamodb.create_table(
        TableName="test-table",
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "job_id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "job_id", "AttributeType": "S"},
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )

    # Mock JWT decode to return a user_id
    mock_jwt_decode.return_value = {"sub": "test-user"}

    # Test the /upload endpoint
    response = client.post(
        "/upload",
        headers={"Authorization": "Bearer fake-token"},
        json={"filename": "test.pdf", "mode": "audio"},
    )

    assert response.status_code == 200
    assert "upload_url" in response.json()
    assert "job_id" in response.json()

    # Verify that the correct calls were made
    mock_jwt_decode.assert_called_once()


def test_generate_upload_url_no_auth():
    response = client.post("/upload", json={"filename": "test.pdf", "mode": "audio"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Authorization header missing"}


@patch("jwt.decode")
def test_generate_upload_url_invalid_token(mock_jwt_decode):
    mock_jwt_decode.side_effect = Exception("Invalid token")

    response = client.post(
        "/upload",
        headers={"Authorization": "Bearer invalid-token"},
        json={"filename": "test.pdf", "mode": "audio"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token: Invalid token"}
