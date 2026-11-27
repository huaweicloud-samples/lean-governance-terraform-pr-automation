# lean-governance-terraform-pr-automation

![cloud](https://img.shields.io/badge/cloud-HuaweiCloud-blue)
![iac](https://img.shields.io/badge/IaC-Terraform-orange)
![License](https://img.shields.io/badge/License-MIT--NoAttribution-green)
> A configuration-driven automation tool for Terraform infrastructure updates — batch-modify parameters across multiple repositories, automatically create Pull Requests, and send notifications via Huawei Cloud SMN (or Slack). The tool is cloud-vendor agnostic and supports Huawei Cloud Terraform (`huaweicloud_*` provider).

## 1. Overview

### Introduction

When managing a large number of Terraform repositories, routine manual parameter updates (upgrading module versions, adjusting resource flavors, correcting security group rule descriptions, etc.) are inefficient and error-prone. This tool declares "which changes to make to which files in which repositories" in a single `config.yaml`, and automatically performs: branch creation → HCL parameter update → `terraform fmt` → commit → PR creation → notification, with the whole flow supporting a `DRY_RUN` preview.

Key point: **the tool itself does not depend on any cloud vendor SDK**; it only parses HCL text and creates PRs through the GitHub API, so it can be used directly with Huawei Cloud Terraform repositories.

---

## 2. Table of Contents

- [1. Overview](#1-overview)
- [2. Table of Contents](#2-table-of-contents)
- [3. Architecture Diagram](#3-architecture-diagram)
- [4. Highlights](#4-highlights)
- [5. Cloud Services Used](#5-cloud-services-used)
- [6. Prerequisites](#6-prerequisites)
- [7. Quick Start](#7-quick-start)
- [8. Step-by-Step Deployment](#8-step-by-step-deployment)
- [9. Usage / Verification](#9-usage--verification)
- [10. Cleanup](#10-cleanup)
- [11. Detailed Explanation](#11-detailed-explanation)
- [12. Dependencies](#12-dependencies)
- [13. FAQ / Troubleshooting](#13-faq--troubleshooting)
- [14. Contributing](#14-contributing)
- [15. License](#15-license)
- [16. Contact / Maintainers](#16-contact--maintainers)

### Directory Structure

```
lean-governance-terraform-pr-automation/
├── README.md
├── docs/ # Huawei Cloud practice documents
│ ├── architecture.md # Architecture description
│ ├── deployment-guide.md # Deployment guide
├── infra/ # Huawei Cloud supporting resource IaC (SMN topic + OBS bucket)
│ ├── provider.tf
│ ├── variables.tf
│ └── main.tf
└── src/ # Tool code
├── main.py # Configuration-driven engine (including SMN broadcast)
├── adapter/
│ └── notification_adapter.py # Huawei Cloud SMN notification backend
├── config.example.yaml # Huawei Cloud Terraform demo configuration
├── requirements.txt
├── requirements-smn.txt # Optional SMN dependencies
└── examples/
└── huaweicloud-test-contents/ # Huawei Cloud Terraform sample repository
```

---

## 3. Architecture Diagram

The relationship between the tool and the infrastructure:

```
┌──────────────┐    ┌──────────────┐
│  GitHub API  │ ←→ │ Python CLI   │
│ (PR / Branch)│    │ (main.py)    │
└──────────────┘    └──────┬───────┘
                           │ Parse HCL / create PR
                           ▼
              ┌────────────────────────┐
              │ Terraform repo list    │
              │ (declared in config.yaml)│
              └────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │ Huawei Cloud support (infra/)│
              │  - SMN notification topic   │
              │  - OBS log/artifact bucket  │
              └────────────────────────┘
```

---

## 4. Highlights

- **Configuration-driven**: `config.yaml` declaratively describes the "repository / file / change" triple
- **Previewable**: `DRY_RUN=true` prints everything that would be changed, without actually writing PRs
- **Cloud-vendor agnostic**: the tool only parses HCL + calls the GitHub API, **without depending on any cloud SDK**
- **Optional SMN notifications**: native integration with Huawei Cloud SMN topics as a notification backend

---

## 5. Cloud Services Used

- SMN (Message Notification Service)
- OBS (Object Storage Service)
- CodeArts Pipeline (optional, for hosting the execution flow)

---

## 6. Prerequisites

- Python 3.8+
- GitHub Personal Access Token (`repo` + `read:org`)
- Terraform CLI (optional, only required for `terraform fmt`)
- The target Terraform repositories already exist and the Token has write permissions
- (Optional) Huawei Cloud credentials: `HW_ACCESS_KEY` / `HW_SECRET_KEY` / `HW_PROJECT_ID` / `HW_REGION_NAME` (only needed when SMN is enabled or `infra/` is used)

---

## 7. Quick Start

```bash
# 1. Install dependencies
cd src
pip3 install -r requirements.txt
# For native SMN notifications: pip3 install -r requirements-smn.txt

# 2. Prepare the configuration
cp config.example.yaml config.yaml
# Edit config.yaml, replacing owner/repo with your GitHub organization and Huawei Cloud Terraform repositories

# 3. Preview (no branches/PRs are actually created)
export GITHUB_TOKEN="your_github_token"
export DRY_RUN=true
python3 main.py

# 4. Run for real (remove DRY_RUN)
unset DRY_RUN
python3 main.py
```

Enable Huawei Cloud SMN notifications (optional):

```bash
export HW_SMN_TOPIC_URN="urn:smn:cn-north-4:<project_id>:tf-pr-automation-notifications"
export HW_PROJECT_ID="<your-project-id>"
export HW_REGION_NAME="cn-north-4"
export HW_ACCESS_KEY="<HW_ACCESS_KEY>"
export HW_SECRET_KEY="<HW_SECRET_KEY>"
```

---

## 8. Step-by-Step Deployment

1. In the `src/` directory, run `pip3 install -r requirements.txt` to install dependencies.
2. Copy `config.example.yaml` to `config.yaml` and fill in the repository list.
3. Set the `GITHUB_TOKEN` environment variable.
4. Preview with `DRY_RUN=true` and confirm the changes are correct.
5. Remove `DRY_RUN` and run for real, automatically creating branches and PRs.
6. (Optional) Run `terraform apply` in `infra/` to create SMN/OBS resources.

---

## 9. Usage / Verification

### Usage and Verification

1. Run with `DRY_RUN=true` and confirm the expected repositories/files are scanned and the intended changes are printed.
2. Run for real on a test repository and confirm branches and PRs are created automatically with correct content.
3. After configuring SMN, confirm that the Huawei Cloud SMN topic (and subscribed email/HTTP endpoints) receive notifications.
4. (Optional) Run `terraform apply` in `infra/` to create the SMN topic and OBS bucket, and upload run logs to OBS in the pipeline.

After deployment, follow these steps to verify that the business functionality works before considering the delivery complete.

---

## 10. Cleanup

```bash
cd infra && terraform destroy
```

---

## 11. Detailed Explanation

- Architecture and components: `docs/architecture.md`
- Full deployment steps: `docs/deployment-guide.md`

---

## 12. Dependencies

- Huawei Cloud Terraform Provider (`huaweicloud`)
- GitHub API (via `PyGithub`)
- Huawei Cloud native services: SMN / OBS

---

## 13. FAQ / Troubleshooting

### FAQ

- For detailed FAQs, see the troubleshooting section of [docs/deployment-guide.md](./docs/deployment-guide.md).

---

## 14. Contributing

Issues and PRs are welcome. Please follow the existing directory structure and code style of the repository.

---

## 15. License

This Huawei Cloud edition is released under the MIT No Attribution license. See [`LICENSE`](LICENSE) for details.

This Huawei Cloud edition is released under the MIT No Attribution license. See [`LICENSE`](LICENSE) for details.

---

## 16. Contact / Maintainers
| Item | Content |
|---|---|
| **Creator** | [dgc-git](https://github.com/dgc-git) |
| **Maintainer** | [dgc-git](https://github.com/dgc-git) |
| **Contact** | GitHub Issues / PR (see [Section 14](#14-contributing)) |
