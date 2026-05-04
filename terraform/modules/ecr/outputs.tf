output "repository_url" {
  description = "aws ecr repository"
  value       = aws_ecr_repository.ecr.repository_url
}