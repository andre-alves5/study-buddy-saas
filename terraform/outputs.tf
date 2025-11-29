output "sqs_url" {
    value = aws_sqs_queue.processing.url
}

output "s3_bucket" {
    value = aws_s3_bucket.data.id
}

output "dynamodb_table" {
    value = aws_dynamodb_table.jobs.name
}

output "cognito_user_pool_id" {
    value = aws_cognito_user_pool.users.id
}

output "cognito_region" {
    value = "us-east-1" # This should be replaced with a variable in a real-world scenario
}
