terraform {
  required_version = ">= 1.6.0"
}

variable "environment" { type = string }
variable "cloud" { type = string, default = "aws" }

output "architecture" {
  value = {
    env        = var.environment
    cloud      = var.cloud
    components = ["load-balancer", "kubernetes", "redis", "mssql", "object-storage", "cdn"]
  }
}
