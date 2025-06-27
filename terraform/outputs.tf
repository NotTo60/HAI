output "linux_ip" {
  value = try(aws_instance.linux.public_ip, "No Linux instance created")
}

output "windows_ip" {
  value = try(aws_instance.windows.public_ip, "No Windows instance created")
} 