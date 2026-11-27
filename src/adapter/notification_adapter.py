"""Huawei Cloud SMN notification backend.

Native replacement for the optional Slack webhook used by the Terraform PR
automation tool. When ``HW_SMN_TOPIC_URN`` is configured, the tool broadcasts the
same notification text to an SMN topic (email / SMS / HTTP / FunctionGraph
subscriptions), replacing the Slack-specific rich blocks with a plain-text/JSON
message that SMN can deliver.

Credentials are read from the environment:

    HW_ACCESS_KEY / HW_SECRET_KEY / HW_SECURITY_TOKEN / HW_PROJECT_ID / HW_REGION_NAME

On Huawei Cloud FunctionGraph or CCE you normally attach an *agency* (委托) and
omit the static AK/SK. In that case inject the agency's temporary credentials via
``HW_SECURITY_TOKEN`` + ``HW_ACCESS_KEY`` / ``HW_SECRET_KEY`` from the runtime
context, or extend this module to read them from the FunctionGraph context object.

The huaweicloud SDK is an **optional** dependency. Install it with
``pip install -r requirements-smn.txt``. If it is missing, ``publish_to_smn``
returns ``False`` and the caller logs a warning without crashing the automation.
"""
from typing import Optional

import os


def publish_to_smn(text: str, subject: Optional[str] = None, topic_urn: Optional[str] = None) -> bool:
    """Publish ``text`` to an SMN topic. Returns True on success, False otherwise.

    Never raises: the automation must keep running even if a notification fails.
    """
    topic_urn = topic_urn or os.environ.get("HW_SMN_TOPIC_URN")
    if not topic_urn:
        return False

    region = os.environ.get("HW_REGION_NAME", "cn-north-4")
    project_id = os.environ.get("HW_PROJECT_ID")
    ak = os.environ.get("HW_ACCESS_KEY")
    sk = os.environ.get("HW_SECRET_KEY")
    token = os.environ.get("HW_SECURITY_TOKEN")  # temporary credential (agency) if present

    if not (ak and sk and project_id):
        # Without credentials we cannot sign the request. On FunctionGraph/CCE an
        # agency should supply these; surface a clear failure instead of crashing.
        print("[SMN] Missing HW_ACCESS_KEY/HW_SECRET_KEY/HW_PROJECT_ID; cannot publish")
        return False

    try:
        from huaweicloudsdkcore.auth.credentials import BasicCredentials
        from huaweicloudsdksmn.v2 import SmnClient, PublishMessageRequest
        from huaweicloudsdksmn.v2.region.smn_region import SmnRegion
    except Exception as imp_err:  # pragma: no cover - optional dependency
        print(f"[SMN] huaweicloud SDK not installed: {imp_err}")
        return False

    try:
        creds = BasicCredentials(ak, sk, project_id)
        if token:
            creds = creds.with_security_token(token)
        client = (
            SmnClient.new_builder()
            .with_credentials(creds)
            .with_region(SmnRegion.value_of(region))
            .build()
        )
        request = PublishMessageRequest(topic_urn=topic_urn)
        request.subject = subject or "Terraform Automation"
        request.message = text
        client.publish_message(request)
        return True
    except Exception as err:  # pragma: no cover - network/SDK failure
        print(f"[SMN] publish failed: {err}")
        return False
