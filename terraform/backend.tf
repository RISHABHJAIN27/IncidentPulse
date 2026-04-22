terraform {
  backend "s3" {
    bucket = "incident-pulse-tfstate"
    key    = "terraform.tfstate"
    region = "ap-south-1"
    dynamodb_table = "terraform-state-lock"
    encrypt = true
  }
}