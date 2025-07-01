output "linux_ip" {
  value = aws_instance.linux.public_ip
}

output "windows_ip" {
  value = aws_instance.windows.public_ip
}

output "linux_ssh_user" {
  value = local.linux_ssh_user
} 