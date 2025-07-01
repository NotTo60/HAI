resource "aws_key_pair" "ec2_user" {
  key_name   = "hai-ci-ec2-user-key"
  public_key = file("${path.module}/ec2_user_rsa.pub")
  tags = {
    ManagedBy = "hai-ci-workflow"
    Environment = "ci-testing"
    WorkflowRunID = var.workflow_run_id
  }
} 