# --- 1. Storage & State ---
resource "aws_s3_bucket" "data" {
  bucket_prefix = var.bucket_prefix
  force_destroy = var.force_destroy
}

resource "aws_dynamodb_table" "jobs" {
  name         = var.dyn_name
  billing_mode = var.dyn_billing_mode
  hash_key     = var.dyn_hash_key
  range_key    = var.dyn_range_key
  attribute {
    name = var.dyn_hash_key
    type = var.dyn_type
  }
  attribute {
    name = var.dyn_range_key
    type = var.dyn_type
  }
}

# --- 2. Event Bus (Queue) ---
resource "aws_sqs_queue" "processing" {
  name                       = var.sqs_name
  visibility_timeout_seconds = var.sqs_visibility_timeout_seconds
}

# --- 3. Authentication (Cognito) ---
resource "aws_cognito_user_pool" "users" {
  name = var.cog_user_name
  auto_verified_attributes = var.cog_user_auto_verified_attributes
  password_policy {
    minimum_length = var.cog_user_minimum_length
    require_numbers = var.cog_user_require_numbers
  }
}

resource "aws_cognito_user_pool_client" "client" {
  name = var.cog_client_name
  user_pool_id = aws_cognito_user_pool.users.id
  explicit_auth_flows = var.cog_client_explicit_auth_flows
}
