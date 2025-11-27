from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from jose import jwt
import boto3
import os
import uuid
import time
import json

app = FastAPI()
s3 = boto3.client("s3")
sqs = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb")

BUCKET = os.getenv("S3_BUCKET")
QUEUE_URL = os.getenv("SQS_QUEUE_URL")
TABLE_NAME = os.getenv("DYNAMODB_TABLE")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_REGION = os.getenv("COGNITO_REGION")


class JobRequest(BaseModel):
    filename: str
    mode: str


async def get_current_user(authorization: str = Header(None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = authorization.split(" ")[1]
    try:
        # In a real app, you'd fetch the JWKS from Cognito and verify the token signature
        # For this example, we'll just decode it.
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded["sub"]
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


@app.post("/upload")
def generate_upload_url(job: JobRequest, user_id: str = Depends(get_current_user)):
    job_id = str(uuid.uuid4())
    key = f"raw/{user_id}/{job_id}/{job.filename}"

    # 1. Generate Presigned URL
    url = s3.generate_presigned_url(
        "put_object", Params={"Bucket": BUCKET, "Key": key}, ExpiresIn=300
    )

    # 2. Save Metadata
    table = dynamodb.Table(TABLE_NAME)
    table.put_item(
        Item={
            "user_id": user_id,
            "job_id": job_id,
            "status": "PENDING",
            "mode": job.mode,
            "s3_key": key,
            "timestamp": int(time.time()),
        }
    )

    # 3. Queue the Job
    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(
            {"user_id": user_id, "job_id": job_id, "key": key, "mode": job.mode}
        ),
    )

    return {"upload_url": url, "job_id": job_id}
