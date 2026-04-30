output "vpc_id" {
  description = "vpc main id"
  value       = aws_vpc.main.id
}
output "public_subnet_ids" {
  description = "public subnet id list"
  value       =  aws_subnet.public[*].id
}
output "private_subnet_ids" {
  description = "private subnet id list"
  value       =  aws_subnet.private[*].id
}