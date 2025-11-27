import json
import os
import boto3
import pytest
from moto import mock_aws
import importlib
from botocore.exceptions import ClientError

# Import the module that needs to be tested
import processor


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
        # We need to reload the processor module under the mock_aws context
        # for the boto3 clients to be mocked.
        importlib.reload(processor)
        yield {
            "s3": boto3.client("s3", region_name="us-east-1"),
            "sqs": boto3.client("sqs", region_name="us-east-1"),
            "dynamodb": boto3.resource("dynamodb", region_name="us-east-1"),
        }


def test_process_job_success(aws, monkeypatch):
    # Setup mock resources
    sqs = aws["sqs"]
    dynamodb = aws["dynamodb"]

    queue = sqs.create_queue(QueueName="test-queue")
    queue_url = queue["QueueUrl"]

    table = dynamodb.create_table(
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

    # Set environment variables for the processor
    monkeypatch.setenv("SQS_QUEUE_URL", queue_url)
    monkeypatch.setenv("DYNAMODB_TABLE", "test-table")
    monkeypatch.setenv("S3_BUCKET", "test-bucket")
    # Reload the processor module to pick up the new environment variables
    importlib.reload(processor)

    # Add an item to the table to be updated
    table.put_item(
        Item={
            "user_id": "test-user",
            "job_id": "test-job",
            "status": "PENDING",
        }
    )

    # Mock SQS message
    msg_body = {
        "user_id": "test-user",
        "job_id": "test-job",
        "key": "test-key",
        "mode": "audio",
    }
    sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(msg_body))
    messages = sqs.receive_message(QueueUrl=queue_url)
    mock_msg = messages["Messages"][0]

    # Process the job
    processor.process_job(mock_msg)

    # Verify that the correct calls were made
    item = table.get_item(Key={"user_id": "test-user", "job_id": "test-job"})["Item"]
    assert item["status"] == "COMPLETED"

    # Verify that the message was deleted
    messages = sqs.receive_message(QueueUrl=queue_url)
    assert "Messages" not in messages


def test_process_job_failure(aws, monkeypatch):
    # Setup mock resources
    sqs = aws["sqs"]
    dynamodb = aws["dynamodb"]

    queue = sqs.create_queue(QueueName="test-queue")
    queue_url = queue["QueueUrl"]

    table = dynamodb.create_table(
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

    # Set environment variables for the processor, but make table name incorrect
    # to cause a failure.
    monkeypatch.setenv("SQS_QUEUE_URL", queue_url)
    monkeypatch.setenv("DYNAMODB_TABLE", "wrong-table-name")
    monkeypatch.setenv("S3_BUCKET", "test-bucket")
    # Reload the processor module to pick up the new environment variables
    importlib.reload(processor)

    # Mock SQS message
    msg_body = {
        "user_id": "test-user",
        "job_id": "test-job",
        "key": "test-key",
        "mode": "audio",
    }

    # Send a message to the queue, but we will process a manually created message
    sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(msg_body))

    mock_msg = {
        "Body": json.dumps(msg_body),
        "ReceiptHandle": "test-receipt-handle",
    }

    # Add an item to the table to be updated
    table.put_item(
        Item={
            "user_id": "test-user",
            "job_id": "test-job",
            "status": "PENDING",
        }
    )

    # Process the job. We expect a ResourceNotFoundException because the table name is wrong.
    # The processor should catch this, try to update the status to FAILED, which will also fail,
    # and the exception will be re-raised.
    with pytest.raises(ClientError) as e:
        processor.process_job(mock_msg)

    assert e.value.response["Error"]["Code"] == "ResourceNotFoundException"

    # Since the table name is wrong, the job status update will fail.
    # The original item should still have the status of 'PENDING'.
    item = table.get_item(Key={"user_id": "test-user", "job_id": "test-job"})["Item"]
    assert item["status"] == "PENDING"

    # Verify that the message was not deleted
    messages = sqs.receive_message(QueueUrl=queue_url)
    assert "Messages" in messages
