resource "null_resource" "check_linux_instance" {
  depends_on = [aws_instance.linux]
  provisioner "local-exec" {
    command = "echo Linux instance created with IP: ${aws_instance.linux.public_ip}"
  }
}

resource "null_resource" "check_windows_instance" {
  depends_on = [aws_instance.windows]
  provisioner "local-exec" {
    command = "echo Windows instance created with IP: ${aws_instance.windows.public_ip}"
  }
} 