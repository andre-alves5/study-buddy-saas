#S3
bucket_prefix = "study-buddy-data-"
force_destroy = true

#DYNAMODB TABLE
dyn_name         = "study-buddy-jobs"
dyn_billing_mode = "PAY_PER_REQUEST"
dyn_hash_key     = "user_id"
dyn_range_key    = "job_id"
dyn_type = "S"

#SQS QUEUE
sqs_name                       = "study-buddy-processing"
sqs_visibility_timeout_seconds = 300

#COGNITO
cog_user_name = "study-buddy-pool"
cog_user_auto_verified_attributes = ["email"]
cog_user_minimum_length = 8
cog_user_require_numbers = true

cog_client_name = "study-buddy-app-client"
cog_client_explicit_auth_flows = ["ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
