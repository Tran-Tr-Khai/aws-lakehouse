output "glue_role_name" {
  description = "IAM role name assumed by AWS Glue jobs."
  value       = aws_iam_role.glue.name
}

output "glue_role_arn" {
  description = "IAM role ARN assumed by AWS Glue jobs."
  value       = aws_iam_role.glue.arn
}
