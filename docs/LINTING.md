# 代码质量工具配置

本项目配置了三个主要的代码质量工具：

## 工具说明

### 1. Ruff - 快速 Python Linter 和 Formatter
- **功能**: 代码检查和格式化
- **速度**: 比 Flake8/Pylint 快 10-100 倍
- **特点**: 集成了多个工具的规则（Flake8, isort, pyupgrade 等）

### 2. Black - Python 代码格式化工具
- **功能**: 统一代码风格
- **特点**: "无妥协"的格式化，减少代码审查中的格式争议

### 3. MyPy - 静态类型检查
- **功能**: 检查类型注解的正确性
- **配置**: 启用了 `--strict` 模式

## 快速使用

### 方式 1: 使用便捷脚本

**Windows:**
```bash
# 检查所有问题（不修复）
scripts\lint.bat check

# 检查并自动修复
scripts\lint.bat fix

# 只运行 Ruff
scripts\lint.bat ruff

# 只运行格式化
scripts\lint.bat format

# 只运行 MyPy
scripts\lint.bat mypy
```

**Linux/Mac:**
```bash
# 检查所有问题（不修复）
bash scripts/lint.sh check

# 检查并自动修复
bash scripts/lint.sh fix

# 只运行 Ruff
bash scripts/lint.sh ruff

# 只运行格式化
bash scripts/lint.sh format

# 只运行 MyPy
bash scripts/lint.sh mypy
```

### 方式 2: 直接使用命令

```bash
# Ruff - 检查代码
uv run ruff check src/ tests/ scripts/

# Ruff - 检查并自动修复
uv run ruff check --fix src/ tests/ scripts/

# Ruff - 格式化代码
uv run ruff format src/ tests/ scripts/

# Black - 格式化代码
uv run black src/ tests/ scripts/

# Black - 只检查不修改
uv run black --check src/ tests/ scripts/

# MyPy - 类型检查
uv run mypy . --strict
```

## 配置说明

所有配置都在 `pyproject.toml` 文件中：

### Ruff 配置
- **行长度**: 100 字符
- **目标版本**: Python 3.8+
- **启用规则**:
  - E/W (pycodestyle)
  - F (pyflakes)
  - I (isort)
  - N (pep8-naming)
  - UP (pyupgrade)
  - B (flake8-bugbear)
  - C4 (flake8-comprehensions)
  - SIM (flake8-simplify)
  - RET (flake8-return)
  - ARG (flake8-unused-arguments)
  - PTH (flake8-use-pathlib)
  - PL (pylint)

### Black 配置
- **行长度**: 100 字符
- **目标版本**: Python 3.8-3.12
- **引号风格**: 双引号

### MyPy 配置
- **模式**: strict
- **特殊处理**: 允许调用无类型提示的外部库（keyboard）

## Git Pre-commit Hooks（可选）

如果想在每次 commit 前自动运行检查：

```bash
# 安装 pre-commit
pip install pre-commit

# 安装 hooks
pre-commit install

# 手动运行所有 hooks
pre-commit run --all-files
```

配置文件：`.pre-commit-config.yaml`

## 编辑器集成

### VS Code

安装扩展：
- Ruff (charliermarsh.ruff)
- Black Formatter (ms-python.black-formatter)
- Pylance (ms-python.vscode-pylance)

在 `.vscode/settings.json` 中添加：
```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },
  "python.linting.mypyEnabled": true,
  "python.linting.enabled": true
}
```

### PyCharm

1. 安装 Ruff 插件
2. Settings → Tools → Black → 启用
3. Settings → Tools → Python Integrated Tools → Type Checker → MyPy

## CI/CD 集成

在 GitHub Actions 中使用：

```yaml
- name: Run linters
  run: |
    uv run ruff check src/ tests/ scripts/
    uv run black --check src/ tests/ scripts/
    uv run mypy . --strict
```

## 常见问题

### Q: Ruff 和 Black 有什么区别？
A: Ruff 是 linter（检查代码问题）+ formatter，Black 是纯 formatter。两者可以一起使用，Ruff 更快但 Black 更成熟。

### Q: 为什么同时用 Ruff 和 Black？
A: Ruff 的格式化功能还在发展中，Black 更稳定。可以只用 Ruff，但建议两者都用以确保最佳效果。

### Q: MyPy 报错怎么办？
A:
1. 检查类型注解是否正确
2. 对于外部库，在 `pyproject.toml` 中添加 `ignore_missing_imports`
3. 使用 `# type: ignore` 注释（谨慎使用）

### Q: 如何忽略特定规则？
A: 在代码中添加注释：
```python
# ruff: noqa: E501
long_line = "very long string..."

# type: ignore
untyped_call()
```

## 推荐工作流

1. **开发时**: 编辑器自动格式化（保存时）
2. **提交前**: 运行 `scripts/lint.bat fix` 或使用 pre-commit hooks
3. **CI/CD**: 运行 `scripts/lint.bat check` 确保代码质量

## 更多信息

- [Ruff 文档](https://docs.astral.sh/ruff/)
- [Black 文档](https://black.readthedocs.io/)
- [MyPy 文档](https://mypy.readthedocs.io/)
