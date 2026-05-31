output "bucket_name" {
  description = "Lakehouse S3 bucket name."
  value       = aws_s3_bucket.lakehouse.bucket
}

output "bucket_arn" {
  description = "Lakehouse S3 bucket ARN."
  value       = aws_s3_bucket.lakehouse.arn
}

output "s3_uri" {
  description = "Lakehouse S3 bucket URI."
  value       = "s3://${aws_s3_bucket.lakehouse.bucket}"
}
