import json
from unittest.mock import patch, MagicMock
from processor import process_job


@patch("processor.boto3")
def test_process_job_success(mock_boto3):
    # Mock SQS, S3, and DynamoDB clients
    mock_sqs_client = MagicMock()
    mock_s3_client = MagicMock()
    mock_dynamodb_resource = MagicMock()
    mock_boto3.client.side_effect = [mock_sqs_client, mock_s3_client]
    mock_boto3.resource.return_value = mock_dynamodb_resource

    # Mock DynamoDB table
    mock_table = MagicMock()
    mock_dynamodb_resource.Table.return_value = mock_table

    # Mock SQS message
    mock_msg = {
        "Body": json.dumps(
            {
                "user_id": "test-user",
                "job_id": "test-job",
                "key": "test-key",
                "mode": "audio",
            }
        ),
        "ReceiptHandle": "test-receipt-handle",
    }

    # Process the job
    process_job(mock_msg)

    # Verify that the correct calls were made
    assert mock_table.update_item.call_count == 2
    mock_sqs_client.delete_message.assert_called_once_with(
        QueueUrl=None,  # QUEUE_URL is None in test environment
        ReceiptHandle="test-receipt-handle",
    )


@patch("processor.boto3")
def test_process_job_failure(mock_boto3):
    # Mock SQS, S3, and DynamoDB clients
    mock_sqs_client = MagicMock()
    mock_s3_client = MagicMock()
    mock_dynamodb_resource = MagicMock()
    mock_boto3.client.side_effect = [mock_sqs_client, mock_s3_client]
    mock_boto3.resource.return_value = mock_dynamodb_resource

    # Mock DynamoDB table to raise an exception
    mock_table = MagicMock()
    mock_table.update_item.side_effect = Exception("DynamoDB error")
    mock_dynamodb_resource.Table.return_value = mock_table

    # Mock SQS message
    mock_msg = {
        "Body": json.dumps(
            {
                "user_id": "test-user",
                "job_id": "test-job",
                "key": "test-key",
                "mode": "audio",
            }
        ),
        "ReceiptHandle": "test-receipt-handle",
    }

    # Process the job
    process_job(mock_msg)

    # Verify that the correct calls were made
    assert mock_table.update_item.call_count == 2  # PROCESSING and FAILED
    mock_sqs_client.delete_message.assert_not_called()
