# 打包说明

本文档说明如何将GIPianoPlayer打包成独立的Windows可执行文件。

## 前置要求

1. Python 3.8+
2. 已安装项目依赖：`uv sync`
3. PyInstaller已安装（作为开发依赖）

## 打包方法

### 方法1: 使用批处理脚本（推荐）

双击运行 `scripts\build.bat` 或在命令提示符中执行：

```cmd
scripts\build.bat
```

### 方法2: 使用PowerShell脚本

在PowerShell中执行：

```powershell
.\scripts\build.ps1
```

### 方法3: 直接使用Python脚本

```bash
python scripts/build.py
```

## 打包过程

打包脚本会自动执行以下步骤：

1. **清理旧文件**：删除之前的 `build/`、`dist/`、`release/` 目录
2. **创建版本信息**：生成 `version_info.txt` 文件
3. **运行PyInstaller**：
   - 创建单文件可执行程序（`--onefile`）
   - 包含所有必要的依赖库
   - 添加隐藏导入（keyboard, pynput, curses）
   - 打包示例文件和文档
4. **创建发布包**：
   - 复制可执行文件到 `release/` 目录
   - 复制文档和示例文件
   - 创建使用说明

## 输出结构

打包完成后，`release/` 目录结构如下：

```
release/
├── GIPianoPlayer.exe    # 主程序（单文件可执行）
├── README.md            # 项目说明
├── 使用说明.txt         # 快速使用指南
├── docs/                # 完整文档
│   ├── QUICKSTART.md
│   ├── USAGE.md
│   └── ...
└── examples/            # 示例文件
    └── sample_score.txt
```

## 打包配置

### PyInstaller参数说明

- `--onefile`: 打包成单个exe文件
- `--console`: 保留控制台窗口（curses需要）
- `--clean`: 清理临时文件
- `--hidden-import`: 添加隐藏导入的模块
- `--add-data`: 添加数据文件（格式：源路径;目标路径）
- `--version-file`: 添加版本信息

### 自定义打包

如需自定义打包配置，编辑 `scripts/build.py` 中的 `build_executable()` 函数。

常见自定义：

1. **添加图标**：
   ```python
   "--icon=icon.ico",
   ```

2. **隐藏控制台窗口**（不推荐，curses需要控制台）：
   ```python
   "--noconsole",
   ```

3. **添加更多数据文件**：
   ```python
   "--add-data=path/to/file;destination",
   ```

## 注意事项

### 1. 管理员权限

打包后的程序**必须以管理员权限运行**，否则：
- 全局快捷键功能无法使用
- keyboard库无法正常工作

### 2. 杀毒软件

某些杀毒软件可能会误报PyInstaller打包的程序。如遇到此问题：
- 添加到杀毒软件白名单
- 使用代码签名证书签名exe文件

### 3. 文件大小

单文件打包会将所有依赖打包进exe，文件较大（约20-30MB）。如需减小体积：
- 使用 `--onedir` 代替 `--onefile`（生成目录而非单文件）
- 使用UPX压缩（`--upx-dir=path/to/upx`）

### 4. 启动速度

单文件打包的程序首次启动会解压临时文件，速度较慢。后续启动会快一些。

## 故障排除

### 问题1: 找不到模块

**错误**: `ModuleNotFoundError: No module named 'xxx'`

**解决**: 在 `build.py` 中添加隐藏导入：
```python
"--hidden-import=xxx",
```

### 问题2: 找不到数据文件

**错误**: 程序运行时找不到文档或示例文件

**解决**: 检查 `--add-data` 参数，确保路径正确。

### 问题3: curses相关错误

**错误**: `_curses module not found`

**解决**: 确保已安装 `windows-curses`：
```bash
uv add windows-curses
```

### 问题4: 打包失败

**解决步骤**:
1. 清理所有临时文件：删除 `build/`、`dist/`、`__pycache__/`
2. 重新安装依赖：`uv sync --reinstall`
3. 检查PyInstaller版本：`uv pip show pyinstaller`
4. 查看详细错误日志

## 高级选项

### 使用spec文件

首次运行PyInstaller后会生成 `GIPianoPlayer.spec` 文件。可以编辑此文件进行更精细的控制：

```bash
pyinstaller GIPianoPlayer.spec
```

### 多平台打包

PyInstaller只能在目标平台上打包。要为其他平台打包：
- Windows: 在Windows上打包
- Linux: 在Linux上打包
- macOS: 在macOS上打包

### 优化打包大小

1. 使用虚拟环境，只安装必要的依赖
2. 使用 `--exclude-module` 排除不需要的模块
3. 使用UPX压缩可执行文件

## 分发

打包完成后，可以分发 `release/` 目录中的所有内容，或者只分发 `GIPianoPlayer.exe`（用户需要自己准备谱面文件）。

建议分发完整的 `release/` 目录，包含：
- 可执行文件
- 文档
- 示例文件
- 使用说明

## 参考资料

- [PyInstaller官方文档](https://pyinstaller.org/)
- [PyInstaller常见问题](https://github.com/pyinstaller/pyinstaller/wiki)
