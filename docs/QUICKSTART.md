# GIPianoPlayer 快速开始指南

## 使用 uv 进行 Python 版本管理

本项目推荐使用 [uv](https://github.com/astral-sh/uv) 进行 Python 版本管理和依赖安装。

### 1. 安装 uv

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 使用 uv 运行项目

uv 会自动管理 Python 版本和虚拟环境：

```bash
# 安装依赖
uv pip install -r requirements.txt

# 或者直接运行（uv 会自动安装依赖）
uv run main.py --gui

# CLI 模式
uv run main.py tests/sample_score.txt
```

### 3. 指定 Python 版本

如果需要特定的 Python 版本：

```bash
# 使用 Python 3.11
uv run --python 3.11 main.py --gui

# 使用 Python 3.12
uv run --python 3.12 main.py --gui
```

### 4. 创建虚拟环境（可选）

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 安装依赖
uv pip install -r requirements.txt

# 运行程序
python main.py --gui
```

## 传统方式（不使用 uv）

如果不使用 uv，可以使用传统的 pip 方式：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py --gui
```

## 使用说明

### GUI 模式（推荐新手）

```bash
uv run main.py --gui
```

1. 点击 "Open File" 选择谱面文件（如 `tests/sample_score.txt`）
2. 调整播放参数（速度、间隔等）
3. 点击 "Play" 开始播放
4. 切换到目标应用窗口（如游戏），脚本会自动输入

### CLI 模式（适合高级用户）

```bash
uv run main.py tests/sample_score.txt
```

**注意**：CLI 模式的全局快捷键需要管理员权限

快捷键：
- `Space`: 播放/暂停
- `Esc`: 停止
- `+/-`: 调整速度
- `[/]`: 调整琶音间隔
- `↑/↓`: 调整行间隔
- `←/→`: 跳转行
- `Q`: 退出

## 运行测试

```bash
# 测试解析器
uv run tests/test_parser.py

# 测试播放器
uv run tests/test_player.py
```

## 常见问题

### Q: 为什么推荐使用 uv？

A: uv 的优势：
- 速度快：比 pip 快 10-100 倍
- 自动管理 Python 版本
- 无需手动创建虚拟环境
- 更好的依赖解析

### Q: 程序只输入文本但没有按下按键？

A: 这是因为缺少 `keyboard` 库。解决方法：

1. **安装 keyboard 库**（推荐）：
   ```bash
   uv pip install keyboard
   ```
   注意：Windows 上可能需要管理员权限运行

2. **使用 GUI 模式**：
   ```bash
   # 以管理员身份运行
   uv run main.py --gui
   ```

`keyboard` 库用于发送原始键盘输入（适合游戏），而 `pynput` 只能输入文本字符。

### Q: keyboard 库安装失败怎么办？

A: `keyboard` 库在某些系统上需要特殊权限：

**Windows**：
- 以管理员身份运行 PowerShell 或 CMD
- 然后执行：`uv pip install keyboard`

**Linux**：
- 使用 sudo：`sudo uv pip install keyboard`
- 或者运行程序时使用 sudo

如果仍然失败，可以只使用 `pynput`（仅支持文本输入，不适合游戏）。

### Q: 如何创建自己的谱面？

A: 参考 `tests/sample_score.txt`，格式说明：

**支持的按键**（共 21 个）：
```
Q W E R T Y U
A S D F G H J
Z X C V B N M
```

**谱面格式**：
- 配置参数在文件开头
- 使用 `------` 分隔配置和谱面
- 单音符：直接写字母（如 `Q W E`）
- 和弦：`(QWE)` 同时按下
- 琶音：`[QWE]` 快速依次按下
- 空格标记：`/` 表示间隔

**注意**：其他字母（I、K、L、O、P 等）会被自动忽略。详见 [KEYS.md](KEYS.md)

### Q: 如何调整播放效果？

A: 在 GUI 中实时调整滑块：
- Speed: 整体播放速度
- Arpeggio Interval: 琶音音符间隔
- Space Interval: 空格标记间隔
- Line Interval: 换行间隔

## 项目结构

```
GIPianoPlayer/
├── src/                    # 源代码
│   ├── config.py          # 配置数据类
│   ├── parser.py          # 谱面解析器
│   ├── keyboard_controller.py  # 键盘控制
│   ├── player.py          # 播放引擎
│   ├── cli.py             # 命令行界面
│   └── gui.py             # 图形界面
├── tests/                  # 测试文件
│   ├── test_parser.py     # 解析器测试
│   ├── test_player.py     # 播放器测试
│   └── sample_score.txt   # 示例谱面
├── main.py                # 程序入口
├── requirements.txt       # 依赖列表
├── README.md             # 详细文档
└── QUICKSTART.md         # 本文件
```

## 下一步

1. 尝试运行示例：`uv run main.py --gui`
2. 打开 `tests/sample_score.txt` 查看谱面格式
3. 创建自己的谱面文件
4. 调整参数以适应你的游戏/应用

祝你使用愉快！🎹
