module "vpc" {
  source  = "../../terraform-modules/modules/vpc"
  cidr    = var.vpc_cidr
  subnet  = var.subnet_cidr
  region  = "cn-north-4"
}
