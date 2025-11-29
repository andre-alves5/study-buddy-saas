import boto3
import os
import json
import time

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
sqs = boto3.client("sqs", region_name=AWS_REGION)
s3 = boto3.client("s3", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
polly = boto3.client("polly", region_name=AWS_REGION)

QUEUE_URL = os.getenv("SQS_QUEUE_URL")
BUCKET = os.getenv("S3_BUCKET")
TABLE_NAME = os.getenv("DYNAMODB_TABLE")


def update_job_status(user_id, job_id, status, error=None):
    table = dynamodb.Table(TABLE_NAME)
    update_expression = "SET #s = :s"
    expression_attribute_names = {"#s": "status"}
    expression_attribute_values = {":s": status}

    if error:
        update_expression += ", #e = :e"
        expression_attribute_names["#e"] = "error"
        expression_attribute_values[":e"] = str(error)

    table.update_item(
        Key={"user_id": user_id, "job_id": job_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values,
    )


def process_job(msg):
    body = json.loads(msg["Body"])
    job_id = body["job_id"]
    user_id = body["user_id"]

    try:
        print(f"Processing Job: {job_id}")
        update_job_status(user_id, job_id, "PROCESSING")

        # 2. Download PDF (Mock logic)
        # pdf_obj = s3.get_object(Bucket=BUCKET, Key=body['key'])
        # text = extract_text(pdf_obj)
        text = "This is a mock summary of the AWS Whitepaper."  # Placeholder

        # 3. Call Bedrock/Polly logic here...
        # (Use the code we wrote in previous chats)

        update_job_status(user_id, job_id, "COMPLETED")

        # 4. Delete Message
        sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"])

    except Exception as e:
        print(f"Error processing job {job_id}: {e}")
        update_job_status(user_id, job_id, "FAILED", error=e)


if __name__ == "__main__":
    # In a production environment, this would be a long-running process
    # managed by a container orchestrator like Kubernetes or ECS,
    # or a serverless function triggered by SQS.
    while True:
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL, MaxNumberOfMessages=1, WaitTimeSeconds=20
        )

        if "Messages" in response:
            process_job(response["Messages"][0])
        else:
            print("Running... No messages.")
