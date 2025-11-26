output "sqs_url" {
    value = aws_sqs_queue.processing.url
}

output "s3_bucket" {
    value = aws_s3_bucket.data.id
}
