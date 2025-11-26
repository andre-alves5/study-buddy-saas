#S3
variable "bucket_prefix" {
  type = string
}

variable "force_destroy" {
  type = bool
}

#DYNAMODB
variable "dyn_name" {
  type = string
}

variable "dyn_billing_mode" {
  type = string
}

variable "dyn_hash_key" {
  type = string
}

variable "dyn_range_key" {
  type = string
}

variable "dyn_type" {
  type = string
}

#SQS QUEUE
variable "sqs_name" {
  type = string
}
variable "sqs_visibility_timeout_seconds" {
  type = number
}

#COGNITO
variable "cog_user_name" {
  type = string
}
variable "cog_user_auto_verified_attributes" {
  type = list(string)
}
variable "cog_user_minimum_length" {
  type = number
}
variable "cog_user_require_numbers" {
  type = bool
}
variable "cog_client_name" {
  type = string
}
variable "cog_client_explicit_auth_flows" {
  type = list(string)
}
