#!/bin/bash
set -eux

# Update system
dnf update -y

# Utilities
dnf install -y nano

# Install CloudWatch Agent
dnf install -y amazon-cloudwatch-agent
systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent