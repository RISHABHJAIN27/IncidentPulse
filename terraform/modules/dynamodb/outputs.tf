output "dynamodb_table_arn" {
    description = "aws dynamodb table arn"
    value = aws_dynamodb_table.incidents.arn
}