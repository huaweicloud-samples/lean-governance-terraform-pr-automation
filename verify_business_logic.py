#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务逻辑本地验证脚本（无需 GitHub / 华为云账号）。

直接调用迁移后工具 src/main.py 的真实函数，逐项断言核心逻辑。
重点：区分真实可用的核心能力 (PASS) 与已知的代码局限 (WARN)。

运行：
  cd <repo>
  GITHUB_TOKEN=dummy python3 verify_business_logic.py
（GITHUB_TOKEN 仅用于让 main.py 顺利 import，不会被发往任何网络）
"""
import os
import sys

# 让 main.py 能 import（main.py 顶层读取 GITHUB_TOKEN，但不会发起网络请求）
os.environ.setdefault("GITHUB_TOKEN", "dummy-token-for-import-only")

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, SRC)

import hcl2  # noqa: E402
import main as M  # noqa: E402

# 用 __new__ 绕过 __init__（__init__ 会调用 Github(token).get_repo 触发网络），
# 只保留函数所需的实例属性。
up = M.TerraformVersionUpdater.__new__(M.TerraformVersionUpdater)
up.changes_made = False
up.error_count = 0

_passed = 0
_failed = 0
_warns = 0


def ok(name, cond, detail=""):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"[PASS] {name}  {detail}")
    else:
        _failed += 1
        print(f"[FAIL] {name}  {detail}")


def warn(name, detail):
    global _warns
    _warns += 1
    print(f"[WARN] {name}  {detail}")


def res_types(parsed):
    """hcl2 把 resource 解析成 list[dict]，统一抽资源类型。"""
    out = []
    for block in parsed.get("resource", []):
        for k in block.keys():
            out.append(k.strip('"'))  # 个别 hcl2 版本会把类型键带上引号
    return out


print("=" * 64)
print("【PASS 组】真实可用的核心能力")
print("=" * 64)

print("\n-- 1) compare_versions：版本比较（支持的 major.minor 范围）--")
ok("1.29 > 1.27", M.compare_versions("1.29", "1.27") == 1,
   f"-> {M.compare_versions('1.29','1.27')}")
ok("1.28 < 1.29", M.compare_versions("1.28", "1.29") == -1,
   f"-> {M.compare_versions('1.28','1.29')}")
ok('"1.6.0" == "1.6.0"', M.compare_versions('"1.6.0"', '"1.6.0"') == 0,
   f"-> {M.compare_versions('1.6.0','1.6.0')}")
ok("1.5.0 < 1.6.0", M.compare_versions("1.5.0", "1.6.0") == -1,
   f"-> {M.compare_versions('1.5.0','1.6.0')}")

print("\n-- 2) update_file(variables)：变量默认值改写（真实改动）--")
var_tf = 'variable "vpc_cidr" {\n  default = "192.168.0.0/16"\n}\n'
with open("temp_file.tf", "w", encoding="utf-8") as f:
    f.write(var_tf)
r = up.update_file("default", "192.168.10.0/16", "variables", "vpc_cidr")
new = open("temp_file.tf", encoding="utf-8").read()
ok("变量 default 被改写", r and ("192.168.10.0/16" in new),
   f"-> changed={r}, 含新值={'192.168.10.0/16' in new}")

print("\n-- 3) update_file(modules)：模块 version 改写（真实改动）--")
mod_tf = 'module "vpc" {\n  source  = "huaweicloud/vpc"\n  version = "1.5.0"\n}\n'
with open("temp_file.tf", "w", encoding="utf-8") as f:
    f.write(mod_tf)
r = up.update_file("version", "1.6.0", "modules", "vpc")
new = open("temp_file.tf", encoding="utf-8").read()
ok("模块 version 被改写", r and ("1.6.0" in new),
   f"-> changed={r}, 含新值={'1.6.0' in new}")

print("\n-- 4) hcl2 解析：华为云资源 / 模块语法兼容（引擎依赖证明）--")
compute_tf = 'resource "huaweicloud_compute_instance" "web" {\n  flavor_id = "s6.large.2"\n}\n'
p1 = hcl2.loads(compute_tf)
ok("解析 huaweicloud_compute_instance", "huaweicloud_compute_instance" in res_types(p1),
   f"-> {res_types(p1)}")
rds_tf = 'resource "huaweicloud_rds_instance" "main" {\n  engine_version = "8.0.28"\n}\n'
p2 = hcl2.loads(rds_tf)
ok("解析 huaweicloud_rds_instance", "huaweicloud_rds_instance" in res_types(p2),
   f"-> {res_types(p2)}")
mod_tf2 = 'module "cce" {\n  source = "huaweicloud/cce"\n}\n'
p3 = hcl2.loads(mod_tf2)
ok("解析 module 块", "module" in p3, f"-> keys={list(p3.keys())}")

print()
print("=" * 64)
print("【WARN 组】已知的代码局限")
print("=" * 64)

print("\n-- W1) compare_versions 仅比较 major.minor，无法区分补丁号 --")
v = M.compare_versions("8.0.28", "8.0.30")
warn("8.0.28 vs 8.0.30 被判为相等",
     f"-> compare_versions 返回 {v}（期望 -1）。原因：正则仅取 \\d+\\.\\d+，"
     f"补丁号被截断。影响：RDS engine_version 8.0.28→8.0.30 的过时检测会失效。")

print("\n-- W2) _extract_key_parameters 正则抽取结果畸形 --")
mod = 'module "vpc" {\n  source  = "huaweicloud/vpc"\n  version = "1.5.0"\n}\n'
prm = M.TerraformVersionUpdater._extract_key_parameters(up, mod)
warn("version 抽取为畸形值", f"-> 抽到 {prm.get('version')!r}（应为 '1.5.0'）")
warn("source 抽取为畸形值", f"-> 抽到 {prm.get('source')!r}（应为 'huaweicloud/vpc'）")

print("\n-- W3) 资源『扁平属性』更新是空操作（stub）--")
ci_tf = 'resource "huaweicloud_compute_instance" "web" {\n  flavor_id = "s6.large.2"\n}\n'
with open("temp_file.tf", "w", encoding="utf-8") as f:
    f.write(ci_tf)
# 模拟主循环对资源的调用方式：update_file(param, to, "resources", "type.name")
r = up.update_file("flavor_id", "c7.large.2", "resources", "huaweicloud_compute_instance.web")
after = open("temp_file.tf", encoding="utf-8").read()
warn("compute flavor_id 实际未被改写",
     f"-> update_file 返回 {r}，文件仍含 's6.large.2'={'s6.large.2' in after}。"
     f"原因：_update_resource_in_hcl 仅按资源类型匹配、不定位属性值即返回 True（stub）。"
     f"config.example.yaml 中 compute/ secgroup/ rds 扁平改动均走此路径，当前不会真正落地。")

print("\n-- W4) 资源『块式嵌套』属性不被点号正则改写 --")
rds_block = 'resource "huaweicloud_rds_instance" "main" {\n  performance_insights_configuration {\n    enabled = false\n  }\n}\n'
new_block = up.process_nested_parameter(
    rds_block, "performance_insights_configuration.enabled", "true",
    "resources", "huaweicloud_rds_instance.main")
warn("块式嵌套 enabled 未被改写",
     f"-> 'enabled = false' 仍在={'enabled = false' in new_block}。"
     f"原因：回退正则只匹配 'a.b = v' 点号赋值形式，不匹配 HCL 块式嵌套。")

print()
print("=" * 64)
print(f"结果: {_passed} 通过 / {_failed} 失败 / {_warns} 项已知局限")
print("=" * 64)
if _failed:
    sys.exit(1)
print("✅ 『变量/模块自动化 + HCL 解析 + 版本比较』核心能力验证通过")
print("⚠ 资源属性更新为已知局限，如需要请补丁修复（见 W3/W4）")
