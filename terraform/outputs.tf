output "configured_region" {
  description = "region configured for terraform resources"
  value       = var.aws_region
}

output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_id" {
  value = aws_subnet.public.id
}

output "private_subnet_id" {
  description = "Private subnet ID"
  value       = aws_subnet.private.id
}

output "security_group_id" {
  value = aws_security_group.web_sg.id
}

output "instance_profile_name" {
  value = aws_iam_instance_profile.ec2_profile.name
}