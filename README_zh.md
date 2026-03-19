# patchon

[![CI](https://github.com/cskujou/patchon/actions/workflows/ci.yml/badge.svg)](https://github.com/cskujou/patchon/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/patchon)](https://pypi.org/project/patchon/)
[![Python](https://img.shields.io/pypi/pyversions/patchon)](https://pypi.org/project/patchon/)

在运行 Python 脚本前自动应用临时源代码补丁，执行完成后自动恢复原文件。

[English README](README.md)

## 为什么需要 patchon？

在开发或调试 Python 应用时，经常需要临时修改库代码：
- 添加日志以了解内部行为
- 在官方修复发布前临时修补 bug
- 注入性能分析探针
- 测试变更而不影响全局环境

`patchon` 提供无缝体验：将补丁作为普通的 `.py` 文件编写，`patchon` 会在运行脚本前自动应用这些补丁，完成后自动恢复原文件。

## 安装

```bash
pip install patchon
```

或使用 `uv`：

```bash
uv add --dev patchon
```

## 基本用法

### 将 `python` 替换为 `patchon`

```bash
# 之前
python myscript.py

# 之后 - 运行前自动应用补丁
patchon myscript.py
```

### 传递参数给脚本

```bash
# 之前
python server.py --port 8000 --debug

# 之后
patchon server.py --port 8000 --debug
```

### 运行模块

```bash
# 之前
python -m http.server 8000

# 之后
patchon -m http.server 8000
```

### 执行命令字符串

```bash
# 之前
python -c "import requests; print(requests.__version__)"

# 之后
patchon -c "import requests; print(requests.__version__)"
```

## 配置

`patchon` 自动从当前目录向上查找配置：

1. 首先查找包含 `[tool.patchon]` 的 `pyproject.toml`
2. 如果没有，则查找 `patchon.yaml`
3. 如果都没有找到，报错

### pyproject.toml（推荐）

```toml
[tool.patchon]
verbose = true
strict = true

[[tool.patchon.patches]]
package = "requests"
expected_version = "2.31.0"
patch_root = "./patches/requests"

[[tool.patchon.patches]]
package = "fastapi"
patch_root = "./patches/fastapi"
```

### patchon.yaml

```yaml
verbose: true
strict: true

patches:
  - package: requests
    expected_version: "2.31.0"
    patch_root: "./patches/requests"

  - package: fastapi
    patch_root: "./patches/fastapi"
```

### 配置字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `verbose` | 布尔值 | 启用详细日志 |
| `strict` | 布尔值 | 设为 `true` 时，任何补丁错误都会导致失败 |
| `package` | 字符串 | 要补丁的包名（必需） |
| `expected_version` | 字符串 | 预期的包版本（可选） |
| `patch_root` | 字符串 | 包含补丁文件的目录（相对于配置文件） |

### 路径解析

`patch_root` 路径相对于配置文件所在目录解析，而不是当前工作目录。这确保了无论从何处运行 `patchon`，行为都是一致的。

例如，使用以下结构：

```
project/
├── pyproject.toml
├── src/
│   └── main.py
└── patches/
    └── requests/
        └── sessions.py
```

如果 `pyproject.toml` 包含 `patch_root = "./patches/requests"`，无论从哪里运行 `patchon`，它都会解析为 `/path/to/project/patches/requests/`。

## CLI 选项

`patchon` 接受自己的选项，其余选项转发给 Python：

```bash
# patchon 选项
patchon --help                    # 显示帮助
patchon --version                 # 显示版本
patchon --check                   # 验证配置
patchon --print-config            # 打印解析后的配置
patchon --dry-run script.py       # 显示将要补丁的内容
patchon --verbose script.py       # 启用详细输出
patchon --quiet script.py         # 抑制非错误输出

# 转发给 Python
patchon -m module                 # 运行模块
patchon -c "command"              # 执行命令字符串
patchon script.py args...         # 运行脚本并传递参数
```

## 安全特性

`patchon` 包含多项安全机制：

- **仅 `.py` 文件**：不会触碰二进制扩展（`.so`、`.pyd` 等）
- **版本检查**：可在补丁前选择性验证包版本
- **文件存在性检查**：补丁前验证目标文件存在
- **自动备份**：修改前备份所有文件
- **保证恢复**：使用 `atexit` 和 `finally` 块确保恢复
- **重复预防**：拒绝在一次会话中两次补丁同一文件
- **新文件警告**：如果 >50% 的补丁是新文件（可能配置错误）则发出警告

## 示例工作流程

1. **确定要补丁的文件**：
   ```bash
   patchon --check
   ```

2. **定位包**：
   ```python
   import requests
   print(requests.__file__)
   # /path/to/site-packages/requests/__init__.py
   ```

3. **创建补丁结构**：
   ```bash
   mkdir -p patches/requests
   ```

4. **复制并修改文件**：
   ```bash
   cp /path/to/site-packages/requests/sessions.py patches/requests/
   # 编辑 patches/requests/sessions.py
   ```

5. **测试补丁**：
   ```bash
   patchon --dry-run myscript.py
   patchon myscript.py
   ```

## 已知限制

- 如果进程被 `SIGKILL`（`kill -9`）终止，无法恢复文件
- 仅支持补丁 `.py` 源文件（不支持二进制扩展）
- Windows 文件锁定可能会阻止某些边缘情况正确恢复
- 不建议同时运行多个 `patchon` 进程对同一包进行补丁

## 开发

### 设置

使用 `uv`（推荐）：

```bash
# 克隆仓库
git clone https://github.com/cskujou/patchon.git
cd patchon

# 同步依赖
uv sync

# 运行测试
uv run pytest

# 本地运行 patchon
uv run patchon --help
```

### 构建

```bash
uv build
```

这会创建 wheel 和 sdist 到 `dist/`。

### 本地安装

```bash
uv run pip install dist/patchon-0.1.0-py3-none-any.whl
```

或直接：

```bash
uv pip install -e .
```

### 发布

#### 使用 `uv` 手动发布

```bash
# 构建并发布到 PyPI
uv build
uv publish
```

您需要先配置 PyPI 凭证：

```bash
uv publish --token $PYPI_TOKEN
# 或
uv publish --username $PYPI_USERNAME --password $PYPI_PASSWORD
```

#### 使用 GitHub Actions 自动发布

查看 `.github/workflows/publish.yml` 了解使用 Trusted Publishing 的自动发布。

## 故障排除

### "No configuration found"

`patchon` 需要配置文件。在项目根目录创建 `pyproject.toml` 或 `patchon.yaml`。

### "Version mismatch"

包版本与 `expected_version` 不匹配。更新您的补丁或移除版本限制。

### "More than 50% of patches are new files"

此警告表明大部分补丁会创建新文件而非修改现有文件。请仔细检查您的 `patch_root` 配置和目录结构。

### 文件未恢复

如果恢复失败（例如进程被终止），您可能需要手动重新安装受影响的包：

```bash
pip install --force-reinstall package_name
```

## 贡献

欢迎贡献！请：

1. Fork 仓库
2. 创建功能分支（`git checkout -b feature/my-feature`）
3. 进行更改
4. 运行测试（`uv run pytest`）
5. 提交更改（`git commit -am 'Add feature'`）
6. 推送到分支（`git push origin feature/my-feature`）
7. 发起 Pull Request

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。
