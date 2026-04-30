module "networking" {
  source = "./modules/networking"

  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
  public_subnet_cidrs = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}
module "ecr" {
  source = "./modules/ecr"

  project_name = var.project_name
  aws_region   = var.aws_region
  environment  = var.environment
}
module "iam" {
  source = "./modules/iam"
  project_name = var.project_name
  environment  = var.environment
 }
module "alb" {
  source = "./modules/alb"

  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
  vpc_id       = module.networking.vpc_id
  public_subnet_ids =module.networking.public_subnet_ids
}
module "dynamodb" {
  source = "./modules/dynamodb"
  project_name = var.project_name
  aws_region   = var.aws_region
  environment  = var.environment
}
module "ecs" {
  source = "./modules/ecs"

  project_name = var.project_name
  aws_region   = var.aws_region
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
}
module "monitoring" {
  source = "./modules/monitoring"

  project_name = var.project_name
  aws_region   = var.aws_region
  environment  = var.environment
}
