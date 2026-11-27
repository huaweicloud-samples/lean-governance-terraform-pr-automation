# ---------------------------------------------------------------------------
# Huawei Cloud support resources for the Terraform PR automation tool.
#
# The tool itself is a provider-agnostic Python CLI (it edits HCL and opens
# GitHub PRs). These resources are the Huawei Cloud-native pieces it relies on
# when run in a Huawei Cloud context:
#   * an SMN topic  -> sends run notifications
#   * an OBS bucket -> stores logs and artifacts
#
# The actual execution environment is a Huawei Cloud CodeArts Pipeline,
# which provides an on-demand build environment. See
# docs/deployment-guide.md for pipeline configuration.
# ---------------------------------------------------------------------------

# Notification topic (native replacement for the Slack webhook).
# Subscribe an email / HTTP / FunctionGraph endpoint out-of-band.
resource "huaweicloud_smn_topic" "notifications" {
  name = var.smn_topic_name
}

# Artifact / log store for the automation run.
# force_destroy keeps the debug bucket easy to tear down.
resource "huaweicloud_obs_bucket" "artifacts" {
  bucket        = var.obs_bucket_name
  force_destroy = true
  storage_class = "STANDARD"
}
