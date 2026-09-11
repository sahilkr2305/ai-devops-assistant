Terraform is an Infrastructure as Code tool used to define and provision infrastructure using configuration files.



\### Basic Workflow

Write Configuration -> terraform init -> terraform plan -> terraform apply



\### Important Commands

terraform init

terraform validate

terraform plan

terraform apply

terraform show

terraform destroy



\### Configuration

Terraform configurations commonly contain:

\- Providers

\- Resources

\- Variables

\- Outputs

\- Modules



Example:



provider "aws" {

&#x20; region = "us-east-1"

}



resource "aws\_instance" "example" {

&#x20; ami           = "ami-example"

&#x20; instance\_type = "t2.micro"

}



\### Terraform State

Terraform state records information about managed infrastructure and helps Terraform determine what changes are required.



\### Best Practices

\- Store Terraform code in Git.

\- Review terraform plan before applying.

\- Protect sensitive variables.

\- Use modules for reusable infrastructure.

\- Avoid hardcoded credentials.

\- Use appropriate remote state for team environments.



\### Safety

terraform apply can create or modify infrastructure.

terraform destroy can permanently delete infrastructure.



An automated DevOps assistant should require explicit approval before infrastructure-changing commands.





