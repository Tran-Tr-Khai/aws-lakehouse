# NYC Taxi Lakehouse Terraform Dev Environment

This directory is the Terraform entry point for the local `dev` environment.

Phase 1 is intentionally a scaffold only. It configures Terraform, the AWS
provider, shared variables, tags, and outputs, but it does not create AWS
resources yet.

## Phase 0: Terraform Basics

Key ideas:

- Provider: plugin Terraform uses to talk to a platform such as AWS.
- Resource: one infrastructure object Terraform can create or manage.
- Variable: input value for reusable configuration.
- Output: value Terraform prints after a plan or apply.
- State: Terraform's record of resources it manages.

State matters. If a resource exists in AWS but is not in Terraform state,
Terraform does not manage it yet. That is why existing AWS resources must be
imported carefully instead of blindly recreated.

## Phase 1: Scaffold

Files in this directory:

```text
versions.tf                 Terraform and provider version constraints
providers.tf                AWS provider configuration
main.tf                     Shared local values and tags
variables.tf                Inputs for this environment
outputs.tf                  Non-sensitive environment summary
terraform.tfvars.example    Example local variable values
```

## First Commands

Install Terraform first, then run:

```bash
cd nyctx-terraform-infra/environments/dev
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform fmt
terraform validate
terraform plan
```

Expected Phase 1 behavior:

- `terraform plan` should not propose creating AWS resources.
- The output should only show `environment_context`.

Do not run `terraform apply` until Phase 2 adds real resources and the plan has
been reviewed.
