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
resource "aws_sqs_queue" "processing_dlq" {
  name = "${var.sqs_name}-dlq"
}

resource "aws_sqs_queue" "processing" {
  name                       = var.sqs_name
  visibility_timeout_seconds = var.sqs_visibility_timeout_seconds
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.processing_dlq.arn
    maxReceiveCount     = 5
  })
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

# --- 4. IAM Roles & Policies ---

# Backend Role
resource "aws_iam_role" "backend" {
  name = "backend-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "ec2.amazonaws.com" # Or your compute service
      }
    }]
  })
}

resource "aws_iam_policy" "backend_policy" {
  name = "backend-policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ],
        Resource = "${aws_s3_bucket.data.arn}/*"
      },
      {
        Effect = "Allow",
        Action = "dynamodb:PutItem",
        Resource = aws_dynamodb_table.jobs.arn
      },
      {
        Effect = "Allow",
        Action = "sqs:SendMessage",
        Resource = aws_sqs_queue.processing.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "backend_attach" {
  role       = aws_iam_role.backend.name
  policy_arn = aws_iam_policy.backend_policy.arn
}

# Worker Role
resource "aws_iam_role" "worker" {
  name = "worker-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "ec2.amazonaws.com" # Or your compute service
      }
    }]
  })
}

resource "aws_iam_policy" "worker_policy" {
  name = "worker-policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ],
        Resource = "${aws_s3_bucket.data.arn}/*"
      },
      {
        Effect = "Allow",
        Action = [
          "dynamodb:UpdateItem",
          "dynamodb:GetItem"
        ],
        Resource = aws_dynamodb_table.jobs.arn
      },
      {
        Effect = "Allow",
        Action = [
            "sqs:ReceiveMessage",
            "sqs:DeleteMessage"
        ],
        Resource = aws_sqs_queue.processing.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "worker_attach" {
  role       = aws_iam_role.worker.name
  policy_arn = aws_iam_policy.worker_policy.arn
}
