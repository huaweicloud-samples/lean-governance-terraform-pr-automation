# 华为云 Terraform PR 自动化工具 — 部署指导书

本指导书说明如何在华为云上下文中部署并运行该 Terraform PR 自动化工具。两种运行方式：**本地 / 跳板机直接运行**（最快验证）与 **华为云 CodeArts 流水线**（生产推荐）。

## 1. 前置条件

- Python 3.8+（已在 3.8/3.9 验证）
- GitHub Personal Access Token（`repo` + `read:org` 权限）—— 工具通过它创建分支与 PR
- 目标 Terraform 仓库已存在且 Token 有写权限
- Terraform CLI（可选，仅 `terraform fmt` 需要）
- （可选）华为云账号与凭证：`HW_ACCESS_KEY` / `HW_SECRET_KEY` / `HW_PROJECT_ID` / `HW_REGION_NAME`——仅当启用 SMN 通知或使用 `infra/` 时需要

## 2. 安装依赖

```bash
cd src
pip3 install -r requirements.txt

# 如需启用 SMN 原生通知，额外安装（可选）:
pip3 install -r requirements-smn.txt

python3 -c "import github; import hcl2; import yaml; import requests; print('依赖安装成功')"
```

## 3. 配置

```bash
cp src/config.example.yaml src/config.yaml
# 编辑 config.yaml：把 owner/repo 改成你的 GitHub 组织与华为云 Terraform 仓库
```

`config.yaml` 中的 `repositories[].files[].changes` 指向 `huaweicloud_*` 资源配置（见 `src/examples/huaweicloud-test-contents/` 中的示例仓库）。

## 4. 本地试运行（验证首选）

```bash
export GITHUB_TOKEN="your_github_token"
export DRY_RUN=true # 只打印将要做的修改，不真正建分支/PR
python3 src/main.py
```

确认输出符合预期后，去掉 `DRY_RUN` 正式运行。

## 5. 华为云 CodeArts 流水线部署（生产推荐）

生产环境推荐使用 **CodeArts 流水线** 触发自动化：

| CodeArts 阶段 | 配置要点 | 说明 |
| --- | --- | --- |
| 手动执行 | 配置 config_file / dry_run / base_branch 等参数 | 按需触发运行 |
| 代码仓拉取 | 关联代码仓 | 获取目标 Terraform 仓库代码 |
| 构建环境 | Python 3.9 + Terraform CLI | 安装运行环境与工具 |
| 依赖安装 | `pip install -r requirements.txt` | 安装 Python 依赖 |
| 执行自动化 | `python3 main.py` | 运行配置更新与 PR 创建 |
| 日志上传 | 上传日志到 **OBS 桶**（本仓库 `infra/` 已建） | 产物落盘 |

流水线变量中注入 `GITHUB_TOKEN`、`SLACK_WEBHOOK_URL` 或 `HW_SMN_TOPIC_URN` + 华为云凭证（建议用 CodeArts 密钥，勿硬编码）。

> 注：CodeArts 流水线的 YAML/JSON 模板因租户与版本而异，本文给出**阶段级映射**而非逐字 YAML，避免猜测性配置。请按你租户的 CodeArts 控制台生成具体流水线定义。

## 6. 配置 SMN 原生通知（可选）

```bash
export HW_SMN_TOPIC_URN="urn:smn:cn-north-4:<project_id>:tf-pr-automation-notifications"
export HW_PROJECT_ID="<your-project-id>"
export HW_REGION_NAME="cn-north-4"
export HW_ACCESS_KEY="<HW_ACCESS_KEY>" # 或使用 FunctionGraph/CCE 委托，省略静态 AK/SK
export HW_SECRET_KEY="<HW_SECRET_KEY>"
```

工具检测到 `HW_SMN_TOPIC_URN` 后即向该 SMN 主题发布纯文本通知（与 Slack 可同时启用）。凭证一律从环境变量注入，**禁止写入任何文件**。

## 7. 部署支持资源（infra/）

`infra/` 提供工具在华为云上下文依赖的两类资源：SMN 主题与 OBS 桶。

```bash
cd infra
terraform init
terraform plan # 仅预览，不产生实际变更
terraform apply # 创建 SMN 主题 + OBS 桶
```

> 提示：`terraform apply` 会创建 SMN 主题与 OBS 桶，长期不用请执行 `terraform destroy` 清理。

## 8. 使用方法验证

1. `DRY_RUN=true` 运行，确认扫描到预期仓库与文件、打印将要修改的内容。
2. 在一个**测试仓库**上正式运行，确认自动创建分支与 PR、内容正确。
3. 配置 SMN 后，确认华为云 SMN 主题收到通知；订阅邮箱/HTTP 可收到对应消息。
4. 确认运行日志可上传到 OBS 桶（若流水线配置了上传步骤）。
