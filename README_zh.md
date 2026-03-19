# patchon

[![CI](https://github.com/cskujou/patchon/actions/workflows/ci.yml/badge.svg)](https://github.com/cskujou/patchon/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/patchon)](https://pypi.org/project/patchon/)
[![Python](https://img.shields.io/pypi/pyversions/patchon)](https://pypi.org/project/patchon/)

`patchon` 读作 `patch-on`。它会在运行你的 Python 代码前临时应用源代码补丁，并在执行结束后把原文件恢复回去。

[English README](README.md)

## 它是做什么的

当你想临时修改已安装 Python 包的源码，但又不想手改 `site-packages`、事后再手动收拾现场时，就可以用 `patchon`。

常见场景包括：

- 给第三方库临时加日志或打印，方便排查问题
- 在上游正式发布修复前先套一个本地 hotfix
- 注入 profiling 或 tracing 代码
- 安全地复现、验证某个针对依赖包的 workaround

## 安装

面向用户的安装方式建议用下面两种之一：

```bash
pip install patchon
```

或者用 `uv` 安装成命令行工具：

```bash
uv tool install patchon
```

安装后，你就可以像用 `python` 一样直接在 shell 里运行 `patchon`。

## 快速开始

### 1. 创建配置

`patchon` 会从当前目录开始向上查找：

1. 带有 `[tool.patchon]` 的 `pyproject.toml`
2. `patchon.yaml`

推荐使用 `pyproject.toml`：

```toml
[tool.patchon]
verbose = true
strict = true

[[tool.patchon.patches]]
package = "requests"
expected_version = "2.31.0"
patch_root = "./patches/requests"
```

你也可以直接从 [`examples/patchon.yaml.example`](examples/patchon.yaml.example) 开始。

### 2. 创建补丁文件

在 `patch_root` 下镜像目标包里的 Python 文件结构。

例如：

```text
your-project/
├── pyproject.toml
└── patches/
    └── requests/
        └── sessions.py
```

如果配置里写的是 `patch_root = "./patches/requests"`，那么 `patchon` 会把：

`patches/requests/sessions.py` -> `requests/sessions.py`

`patch_root` 是相对于配置文件所在目录解析的，不是相对于你当前打开 shell 的目录。

### 3. 用 `patchon` 运行代码

```bash
patchon myscript.py
```

原本你可能会这样运行：

```bash
python myscript.py
```

它也支持模块模式和 `-c` 命令：

```bash
patchon -m http.server 8000
patchon -c "import requests; print(requests.__version__)"
patchon server.py --port 8000 --debug
```

## 一个典型工作流

1. 找到你要 patch 的包文件
2. 把对应的 `.py` 文件复制到本地补丁目录
3. 修改这份本地副本
4. 用 `patchon` 运行目标命令
5. 等运行结束后让 `patchon` 自动恢复原文件

示例：

```bash
python -c "import requests; print(requests.__file__)"
mkdir -p patches/requests
cp /path/to/site-packages/requests/sessions.py patches/requests/
patchon --dry-run myscript.py
patchon myscript.py
```

## 常用命令

这些命令最常用：

```bash
patchon --help
patchon --version
patchon --check
patchon --print-config
patchon --dry-run myscript.py
patchon --cleanup-status
patchon --cleanup
```

`patchon` 会先解析自己的参数，再把剩余参数转发给 Python。

## 安全行为

`patchon` 的设计目标是“临时、可回滚”的源码补丁：

- 只处理 `.py` 文件
- 修改前先备份
- 正常退出时自动恢复
- 可通过 `expected_version` 做版本校验
- 当补丁目录结构可疑时给出警告
- 尽量避免多个 patch 会话互相冲突

## 排查问题

### 找不到配置

请创建带有 `[tool.patchon]` 的 `pyproject.toml`，或创建 `patchon.yaml`。

### 版本不匹配

当前安装的包版本和 `expected_version` 不一致。可以更新补丁，或者在不需要该校验时去掉版本约束。

### 文件没有恢复

如果进程被强行杀掉，可以先执行：

```bash
patchon --cleanup
```

必要时重新安装受影响的包：

```bash
pip install --force-reinstall package_name
```

## 更多文档

- [English README](README.md)
- [安装](docs/docs/getting-started/installation.md)
- [配置](docs/docs/getting-started/configuration.md)
- [进阶指南](docs/docs/user-guide/advanced.md)

## 开发

如果你是想参与 `patchon` 本身的开发，更深入的构建和贡献说明在 `docs/` 与 `.github/` 里。

## 许可证

MIT License，详见 [LICENSE](LICENSE)。
