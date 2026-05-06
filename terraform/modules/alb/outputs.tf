output "alb_security_group_id" {
  description = "alb security group id"
  value       = aws_security_group.alb.id
}
output "target_group_arn" {
    description = "aws alb target group arn"
    value = aws_lb_target_group.main.arn
}