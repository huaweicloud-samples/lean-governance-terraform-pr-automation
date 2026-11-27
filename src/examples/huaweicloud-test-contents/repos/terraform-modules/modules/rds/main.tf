resource "huaweicloud_rds_instance" "main" {
  name           = "demo-rds"
  flavor         = "rds.mysql.s1.large"
  vpc_id         = var.vpc_id
  subnet_id      = var.subnet_id
  engine         = "MySQL"
  engine_version = "8.0" # automation will bump this to 8.0.30

  performance_insights_configuration {
    enabled = false # automation will flip this to true
  }
}
