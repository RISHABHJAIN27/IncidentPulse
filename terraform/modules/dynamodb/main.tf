resource "aws_dynamodb_table" "incidents" {
  name         = "incidents"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Name    = "${var.project_name}-incidents-table"
    Project = var.project_name
  }
}