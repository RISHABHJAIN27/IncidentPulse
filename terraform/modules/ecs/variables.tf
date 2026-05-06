variable "project_name" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_cidr" {
  type = string
}
variable "alb_security_group_id" {
  type = string
}
variable "vpc_id" {
  type = string
}
variable "repository_url" {
  type = string
}
variable "task_execution_arn" {
  type = string
}
variable "task_arn" {
  type = string
}
variable "target_group_arn"{
  type = string
}
variable "private_subnet_ids"{
type = list(string)
}