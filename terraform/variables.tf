variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "incident-pulse"
}
variable "aws_region" {
  description = "Region of AWS"
  type        = string
  default     = "ap-south-1"
}
variable "environment" {
  description = "Environment of AWS"
  type        = string
  default     = "production"
}
variable "vpc_cidr" {
  description = "cidr of vpc"
  type        = string
  default     = "10.0.0.0/16"
}
variable "public_subnet_cidrs" {
  description = "CIDR ranges for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR ranges for private subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}


