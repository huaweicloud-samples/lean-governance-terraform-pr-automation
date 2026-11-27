variable "cluster_version" {
  type    = string
  default = "1.28"
}

variable "node_flavor" {
  type    = list(string)
  default = ["s6.large.2"]
}
