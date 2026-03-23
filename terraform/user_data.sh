#!/bin/bash
set -eux

# Update system
dnf update -y

# Utilities
dnf install -y nano

# Install nginx
dnf install -y nginx
systemctl enable nginx
systemctl start nginx

# Install CloudWatch Agent
dnf install -y amazon-cloudwatch-agent

# Start agent (basic start for now)
systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent