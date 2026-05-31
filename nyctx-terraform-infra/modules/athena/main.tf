resource "aws_athena_workgroup" "pipeline" {
  name          = var.pipeline_workgroup_name
  force_destroy = var.force_destroy

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = var.pipeline_output_location
    }
  }
}

resource "aws_athena_workgroup" "dbt" {
  name          = var.dbt_workgroup_name
  force_destroy = var.force_destroy

  configuration {
    enforce_workgroup_configuration    = false
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = var.dbt_output_location
    }
  }
}
