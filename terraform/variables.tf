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


