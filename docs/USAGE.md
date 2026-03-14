# 使用说明

## 快速开始

### 1. 安装依赖

```bash
# 使用 uv（推荐）
uv pip install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt
```

**重要**：Windows 上需要以管理员身份运行来安装和使用 `keyboard` 库。

### 2. 运行程序

#### GUI 模式（推荐）

```bash
# 以管理员身份运行
uv run main.py --gui
```

1. 点击 "Open File" 选择谱面文件
2. 调整播放参数
3. 点击 "Play" 开始播放
4. 切换到游戏窗口，程序会自动输入按键

#### CLI 模式

```bash
# 以管理员身份运行
uv run main.py "谱面文件路径.qymusic"
```

快捷键：
- `Space`: 播放/暂停
- `Esc`: 停止
- `+/-`: 调整速度
- `Q`: 退出

### 3. 支持的按键

程序只支持以下 21 个按键：

```
Q W E R T Y U
A S D F G H J
Z X C V B N M
```

谱面中的其他字母会被自动忽略。

### 4. 谱面格式

```
# 配置（第一行是版本号）
1.4
ARPEGGIO_INTERVAL=0.05
INTERVAL_RATING=0.1
SPACE_INTERVAL_RATING=1
LINE_INTERVAL_RATING=0
------

# 谱面内容
(VAH)   /H Q /(BSJ)   /H G /
(CMG)   /S   /(CND)   /G D /
```

- `Q` - 单个按键
- `(QWE)` - 和弦（同时按下）
- `[QWE]` - 琶音（快速依次按下）
- `/` - 空格间隔

## 常见问题

### Q: 程序只输入文本不按键？

A: 需要安装 `keyboard` 库并以管理员身份运行：

```bash
# Windows - 以管理员身份打开 PowerShell
uv pip install keyboard
uv run main.py --gui
```

### Q: 如何调整播放效果？

A: 在 GUI 中使用滑块实时调整：
- **Speed**: 整体播放速度（0.1x - 3.0x）
- **Arpeggio Interval**: 琶音音符间隔（0.01s - 0.2s）
- **Space Interval**: 空格标记间隔倍率
- **Line Interval**: 换行间隔倍率

### Q: 谱面中有无效字符怎么办？

A: 程序会自动过滤无效字符，只保留有效的 21 个按键。无需手动修改谱面文件。

### Q: 如何测试程序是否正常工作？

A:
1. 打开记事本（Notepad）
2. 运行程序：`uv run main.py tests/sample_score.txt`
3. 等待 3 秒后切换到记事本窗口
4. 观察是否有按键输入

## 文件说明

- `main.py` - 程序入口
- `src/` - 源代码目录
  - `parser.py` - 谱面解析器
  - `player.py` - 播放引擎
  - `keyboard_controller.py` - 键盘控制
  - `cli.py` - 命令行界面
  - `gui.py` - 图形界面
- `tests/` - 测试文件
  - `sample_score.txt` - 示例谱面
- `README.md` - 详细文档
- `QUICKSTART.md` - 快速开始指南
- `KEYS.md` - 按键说明
- `USAGE.md` - 本文件

## 技巧

1. **调整速度**：先用较慢的速度（0.5x）测试，确认无误后再加速
2. **调整间隔**：根据游戏的响应速度调整各种间隔参数
3. **使用 GUI**：GUI 模式可以实时调整参数，更方便
4. **测试谱面**：使用记事本测试新谱面，确认按键输入正确

## 注意事项

1. **管理员权限**：Windows 上必须以管理员身份运行
2. **焦点切换**：播放时需要将焦点切换到目标窗口（游戏）
3. **按键延迟**：如果游戏响应慢，增加 INTERVAL_RATING 参数
4. **有效按键**：只使用 21 个有效按键，其他字母会被忽略

祝你使用愉快！🎹
