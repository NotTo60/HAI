variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "availability_zone" {
  description = "Availability zone for resources"
  type        = string
  default     = "us-east-1a"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "instance_type_linux" {
  description = "EC2 instance type for Linux"
  type        = string
  default     = "t3.micro"
}

variable "instance_type_windows" {
  description = "EC2 instance type for Windows"
  type        = string
  default     = "t3.micro"
}

variable "windows_password" {
  description = "Password for Windows Administrator user"
  type        = string
  sensitive   = true
  default     = "TemporaryPassword123!"  # Default password if not provided
}

variable "workflow_run_id" {
  description = "Unique ID for the current workflow run"
  type        = string
  default     = "manual-run"  # Default for manual runs
} 