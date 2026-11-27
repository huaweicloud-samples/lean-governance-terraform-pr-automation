resource "huaweicloud_vpc" "this" {
  name = "demo-vpc"
  cidr = var.cidr
}

resource "huaweicloud_vpc_subnet" "this" {
  name       = "demo-subnet"
  cidr       = var.subnet
  vpc_id     = huaweicloud_vpc.this.id
  gateway_ip = cidrhost(var.subnet, 1)
}
