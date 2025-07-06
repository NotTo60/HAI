resource "aws_key_pair" "ec2_user" {
  key_name   = "hai-ci-ec2-user-key"
  public_key = file("${path.module}/ec2_user_rsa.pub")
  tags = {
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
    WorkflowRunID = var.workflow_run_id
  }
}

resource "aws_key_pair" "windows" {
  key_name   = "hai-ci-windows-key"
  public_key = file("${path.module}/windows_rsa.pub")
  tags = {
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
    WorkflowRunID = var.workflow_run_id
  }
} 