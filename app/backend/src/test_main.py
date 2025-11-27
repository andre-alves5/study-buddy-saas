from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
import jwt

client = TestClient(app)


@patch("main.boto3")
@patch("jwt.decode")
def test_generate_upload_url_success(mock_jwt_decode, mock_boto3):
    # Mock JWT decode to return a user_id
    mock_jwt_decode.return_value = {"sub": "test-user"}

    # Mock S3, SQS, and DynamoDB clients
    mock_s3_client = MagicMock()
    mock_sqs_client = MagicMock()
    mock_dynamodb_resource = MagicMock()
    mock_boto3.client.side_effect = [mock_s3_client, mock_sqs_client]
    mock_boto3.resource.return_value = mock_dynamodb_resource

    # Mock S3 presigned URL generation
    mock_s3_client.generate_presigned_url.return_value = "http://s3-presigned-url"

    # Mock DynamoDB table
    mock_table = MagicMock()
    mock_dynamodb_resource.Table.return_value = mock_table

    # Test the /upload endpoint
    response = client.post(
        "/upload",
        headers={"Authorization": "Bearer fake-token"},
        json={"filename": "test.pdf", "mode": "audio"},
    )

    assert response.status_code == 200
    assert "upload_url" in response.json()
    assert "job_id" in response.json()
    assert response.json()["upload_url"] == "http://s3-presigned-url"

    # Verify that the correct calls were made
    mock_jwt_decode.assert_called_once()
    mock_s3_client.generate_presigned_url.assert_called_once()
    mock_table.put_item.assert_called_once()
    mock_sqs_client.send_message.assert_called_once()


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
