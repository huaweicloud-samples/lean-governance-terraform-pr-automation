# Demo target resources for the Huawei Cloud Terraform PR automation tool.
# The automation edits values in this file (e.g. bumps flavor_id / rule descriptions).

resource "huaweicloud_compute_instance" "web" {
  name              = "web-server"
  flavor_id         = "s6.large.2" # automation will bump this to c7.large.2
  image_id          = "1234abcd-5678-90ef-ghij-klmnopqrstuv"
  security_group_ids = [huaweicloud_networking_secgroup.web.id]
  availability_zone = "cn-north-4a"

  network {
    uuid = huaweicloud_vpc_subnet.demo.id
  }
}

resource "huaweicloud_networking_secgroup" "web" {
  name        = "web-sg"
  description = "web tier security group"
}

resource "huaweicloud_networking_secgroup_rule" "allow_web" {
  direction         = "ingress"
  ethertype         = "IPv4"
  protocol          = "tcp"
  port_range_min    = 443
  port_range_max    = 443
  remote_ip_prefix  = "0.0.0.0/0"
  security_group_id = huaweicloud_networking_secgroup.web.id
  description       = "allow inbound from web tier"
}
