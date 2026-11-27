variable "region" {
  description = "Huawei Cloud region to deploy the automation support resources into."
  type        = string
  default     = "cn-north-4"
}

variable "obs_bucket_name" {
  description = "Globally unique OBS bucket name for automation artifacts and run logs."
  type        = string
  default     = "tf-pr-automation-artifacts"
}

variable "smn_topic_name" {
  description = "SMN topic name used for automation notifications (Slack webhook alternative)."
  type        = string
  default     = "tf-pr-automation-notifications"
}
