output "ecs_cluster_name" {
  description = "aws ecs cluster name"
  value       = aws_ecs_cluster.main.name
}
output "ecs_service_name" {
  description = "aws_ecs_service"
  value       = aws_ecs_service.main.name
}