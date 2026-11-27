# lean-governance-terraform-pr-automation · 华为云 Terraform PR 自动化工具

![cloud](https://img.shields.io/badge/cloud-HuaweiCloud-blue)
![iac](https://img.shields.io/badge/IaC-Terraform-orange)
![License](https://img.shields.io/badge/License-MIT--NoAttribution-green)
> 配置驱动的 Terraform 基础设施更新自动化工具——跨多个仓库批量修改参数、自动创建 Pull Request，并以华为云 SMN（或 Slack）发送通知。工具与云厂商无关，已适配华为云 Terraform（`huaweicloud_*` provider）。

## 1. 简介 / Overview

### 简介


在管理大量 Terraform 仓库时，常规的手动参数更新（升级模块版本、调整资源规格、修正安全组规则描述等）既低效又易错。本工具通过一份 `config.yaml` 声明「对哪些仓库的哪些文件做哪些修改」，自动完成：分支创建 → HCL 参数更新 → `terraform fmt` → 提交 → 开 PR → 通知，全流程可 `DRY_RUN` 预演。

关键点：**工具本身不依赖任何云厂商 SDK**，它只解析 HCL 文本并通过 GitHub API 建 PR，因此可直接用于华为云 Terraform 仓库。

---

## 2. 目录

- [1. 简介 / Overview](#1-简介--overview)
- [2. 目录](#2-目录)
- [3. 架构图](#3-架构图)
- [4. 方案亮点](#4-方案亮点)
- [5. 涉及云服务](#5-涉及云服务)
- [6. 前置条件](#6-前置条件)
- [7. 快速开始](#7-快速开始)
- [8. 分步部署](#8-分步部署)
- [9. 使用方法 / 验证](#9-使用方法--验证)
- [10. 清理资源](#10-清理资源)
- [11. 详细说明](#11-详细说明)
- [12. 依赖](#12-依赖)
- [13. FAQ / 故障排除](#13-faq--故障排除)
- [14. 贡献指南](#14-贡献指南)
- [15. 许可证](#15-许可证)
- [16. 联系方式 / 维护者](#16-联系方式--维护者)

### 目录结构


```
lean-governance-terraform-pr-automation/
├── README.md
├── docs/ # 华为云实践文档
│ ├── architecture.md # 架构说明
│ ├── deployment-guide.md # 部署指导书
├── infra/ # 华为云支撑资源 IaC (SMN 主题 + OBS 桶)
│ ├── provider.tf
│ ├── variables.tf
│ └── main.tf
└── src/ # 工具代码
├── main.py # 配置驱动引擎（含 SMN 广播）
├── adapter/
│ └── notification_adapter.py # 华为云 SMN 通知后端
├── config.example.yaml # 华为云 Terraform 演示配置
├── requirements.txt
├── requirements-smn.txt # SMN 可选依赖
└── examples/
└── huaweicloud-test-contents/ # 华为云 Terraform 示例仓库
```

---

## 3. 架构图

工具与基础设施的关系：

```
┌──────────────┐    ┌──────────────┐
│  GitHub API  │ ←→ │ Python CLI   │
│ (PR / Branch)│    │ (main.py)    │
└──────────────┘    └──────┬───────┘
                           │ 解析 HCL / 提 PR
                           ▼
              ┌────────────────────────┐
              │ Terraform 仓库清单      │
              │ (config.yaml 声明)     │
              └────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │ 华为云支撑资源 (infra/) │
              │  - SMN 通知主题        │
              │  - OBS 日志/产物桶    │
              └────────────────────────┘
```

---

## 4. 方案亮点

- **配置驱动**：`config.yaml` 声明式描述「仓库 / 文件 / 修改」三元组
- **可预演**：`DRY_RUN=true` 模式打印所有将要修改，不真正写 PR
- **云厂商无关**：工具只解析 HCL + 调用 GitHub API，**不依赖任何云 SDK**
- **可选 SMN 通知**：原生集成华为云 SMN 主题作为通知后端

---

## 5. 涉及云服务

- SMN（消息通知服务）
- OBS（对象存储服务）
- CodeArts Pipeline（可选，用于承载执行流）

---

## 6. 前置条件

- Python 3.8+
- GitHub Personal Access Token（`repo` + `read:org`）
- Terraform CLI（可选，仅 `terraform fmt` 需要）
- 目标 Terraform 仓库已存在且 Token 有写权限
- （可选）华为云凭证：`HW_ACCESS_KEY` / `HW_SECRET_KEY` / `HW_PROJECT_ID` / `HW_REGION_NAME`（仅启用 SMN 或使用 `infra/` 时需要）

---

## 7. 快速开始

```bash
# 1. 安装依赖
cd src
pip3 install -r requirements.txt
# 如需 SMN 原生通知: pip3 install -r requirements-smn.txt

# 2. 准备配置
cp config.example.yaml config.yaml
# 编辑 config.yaml，把 owner/repo 改为你的 GitHub 组织与华为云 Terraform 仓库

# 3. 预演（不真正建分支/PR）
export GITHUB_TOKEN="your_github_token"
export DRY_RUN=true
python3 main.py

# 4. 正式运行（去掉 DRY_RUN）
unset DRY_RUN
python3 main.py
```

启用华为云 SMN 通知（可选）：

```bash
export HW_SMN_TOPIC_URN="urn:smn:cn-north-4:<project_id>:tf-pr-automation-notifications"
export HW_PROJECT_ID="<your-project-id>"
export HW_REGION_NAME="cn-north-4"
export HW_ACCESS_KEY="<HW_ACCESS_KEY>"
export HW_SECRET_KEY="<HW_SECRET_KEY>"
```

---

## 8. 分步部署

1. 在 `src/` 目录执行 `pip3 install -r requirements.txt` 安装依赖。
2. 复制 `config.example.yaml` 为 `config.yaml` 并填写仓库清单。
3. 设置 `GITHUB_TOKEN` 环境变量。
4. 以 `DRY_RUN=true` 预演，确认修改正确。
5. 去掉 `DRY_RUN` 正式运行，自动创建分支与 PR。
6. （可选）在 `infra/` 下执行 `terraform apply` 创建 SMN/OBS 资源。

---

## 9. 使用方法 / 验证

### 使用方法与验证


1. `DRY_RUN=true` 运行，确认扫描到预期仓库/文件并打印将要修改的内容。
2. 在一个测试仓库上正式运行，确认自动创建分支与 PR、内容正确。
3. 配置 SMN 后，确认华为云 SMN 主题（及订阅的邮箱/HTTP）收到通知。
4. （可选）`infra/` 下 `terraform apply` 创建 SMN 主题与 OBS 桶，并在流水线中将运行日志上传到 OBS。

部署完成后请按本节步骤自行验证，确认业务功能可用，方可视为交付完成。

---

## 10. 清理资源

```bash
cd infra && terraform destroy
```

---

## 11. 详细说明

- 架构与组件：`docs/architecture.md`
- 完整部署步骤：`docs/deployment-guide.md`

---

## 12. 依赖

- 华为云 Terraform Provider (`huaweicloud`)
- GitHub API（通过 `PyGithub`）
- 华为云原生服务：SMN / OBS

---

## 13. FAQ / 故障排除

### FAQ

- 详细 FAQ 见 [docs/deployment-guide.md](./docs/deployment-guide.md) 的排障章节。

---

## 14. 贡献指南

欢迎提交 Issue 与 PR。请遵循仓库内现有目录结构与代码风格。

---

## 15. 许可证

本华为云适配版本以 MIT No Attribution 许可证发布，详见 [`LICENSE`](LICENSE)。


本华为云适配版本以 MIT No Attribution 许可证发布，详见 [`LICENSE`](LICENSE)。

---

## 16. 联系方式 / 维护者
| 项 | 内容 |
|---|---|
| **创建者** | [dgc-git](https://github.com/dgc-git) |
| **维护者** | [dgc-git](https://github.com/dgc-git) |
| **联系方式** | GitHub Issues / PR（见[第 14 节](#14-贡献指南)） |
