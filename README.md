# GIPianoPlayer

一个用于自动弹奏钢琴的Python脚本，可以读取特定格式的文本文件并通过模拟键盘输入来"弹奏"。

## 📚 文档

- [快速开始](docs/QUICKSTART.md) - 快速上手指南
- [使用说明](docs/USAGE.md) - 详细使用文档
- [按键说明](docs/KEYS.md) - 支持的按键列表
- [CLI配置](docs/CLI_CONFIG.md) - 命令行配置说明
- [CLI输出](docs/CLI_OUTPUT.md) - 命令行界面说明
- [显示指南](docs/DISPLAY_GUIDE.md) - 显示相关说明
- [时间控制](docs/TIMING.md) - 时间和节奏控制
- [自定义](docs/CUSTOMIZATION.md) - 自定义配置
- [性能优化](docs/OPTIMIZATION.md) - 性能优化建议
- [更新日志](docs/CHANGELOG.md) - 版本更新记录
- [开发指南](CLAUDE.md) - 给Claude Code的开发指南

## 功能特性

- 📝 解析特定格式的谱面文本文件
- 🎹 支持单音、和弦、琶音等多种弹奏模式
- ⌨️ 通过键盘输入模拟实现自动弹奏
- 🎮 提供CLI和GUI两种界面
- ⏯️ 完整的播放控制（播放/暂停/停止）
- ⚡ 实时调整播放速度和各种间隔参数
- 🔧 完善的类型注解

## 安装

1. 克隆或下载此项目

2. 安装依赖：
```bash
pip install -r requirements.txt
```

**注意**：`keyboard` 库在某些系统上需要管理员权限。如果遇到权限问题，可以只安装 `pynput`，GUI模式不需要 `keyboard` 库。

## 谱面文件格式

谱面文件由两部分组成：配置参数和谱面内容。

### 支持的按键

**重要**：程序只支持以下 21 个按键（游戏键盘布局）：

```
Q W E R T Y U
A S D F G H J
Z X C V B N M
```

其他字母（如 I、K、L、O、P 等）会被自动忽略。详见 [docs/KEYS.md](docs/KEYS.md)

### 配置参数

```
version = 1.0
ARPEGGIO_INTERVAL = 0.05
INTERVAL_RATING = 0.2
SPACE_INTERVAL_RATING = 1.0
LINE_INTERVAL_RATING = 0.0
```

- `version`: 版本号
- `ARPEGGIO_INTERVAL`: 琶音音符之间的间隔（秒）
- `INTERVAL_RATING`: 基础音符间隔倍率
- `SPACE_INTERVAL_RATING`: 空格标记的间隔倍率
- `LINE_INTERVAL_RATING`: 换行间隔倍率

### 谱面内容

支持以下符号：

- **单音符**：直接写字母，如 `Q W E`
- **和弦**：用圆括号包裹，如 `(QWE)` 表示同时按下Q、W、E三个键
- **琶音**：用方括号包裹，如 `[QWE]` 表示快速依次按下Q、W、E
- **嵌套**：支持和弦与琶音的嵌套，如 `[(QW)E]` 表示先同时按QW，然后按E
- **空音（休止符）**：空格表示一个空音（不按键，但占据一个音符的位置）
- **分隔符**：`/` 只是视觉分隔符，用于分组，不影响播放
- **换行**：每行之间会有换行间隔（如果 LINE_INTERVAL_RATING > 0）

示例：
```
(VAH)   /H Q /(BSJ)   /H G /
(CMG)   /S   /(CND)   /G D /
(XS)   /N A /(BG)   /(XS)   /
```

解析后（`/` 被忽略，空格是空音）：
```
(VAH) _ _ _ H Q _ (BSJ) _ _ _ H G _
```

**重要**：
- 每个音符（单音、和弦、琶音、空音）之间都有 INTERVAL_RATING 的间隔
- **空格是空音**，占据一个音符位置但不按键
- **`/` 只是视觉分隔符**，不是音符，会被忽略
- 这样保证了节奏的一致性

## 使用方法

### GUI模式（推荐）

启动图形界面：

```bash
python main.py --gui
```

在GUI中：
1. 点击"Open File"选择谱面文件
2. 使用滑块调整播放参数
3. 点击"Play"开始播放
4. 可以随时暂停、停止或调整参数

### CLI模式

使用命令行界面：

```bash
python main.py tests/sample_score.txt
```

**快捷键**（需要管理员权限）：
- `Space`: 播放/暂停
- `Esc`: 停止
- `+/-`: 调整播放速度
- `[/]`: 调整琶音间隔
- `↑/↓`: 调整换行间隔
- `←/→`: 跳转到上一行/下一行
- `Q`: 退出

## 项目结构

```
GIPianoPlayer/
├── src/
│   ├── __init__.py
│   ├── config.py              # 配置数据类
│   ├── parser.py              # 谱面解析器
│   ├── keyboard_controller.py # 键盘控制器
│   ├── player.py              # 播放引擎
│   ├── cli.py                 # 命令行界面
│   └── gui.py                 # 图形界面
├── tests/
│   ├── __init__.py
│   ├── test_parser.py         # 解析器测试
│   ├── test_player.py         # 播放器测试
│   └── sample_score.txt       # 示例谱面
├── main.py                    # 程序入口
├── requirements.txt           # 依赖列表
└── README.md                  # 说明文档
```

## 运行测试

测试解析器：
```bash
python tests/test_parser.py
```

测试播放器：
```bash
python tests/test_player.py
```

## 注意事项

1. **权限问题**：CLI模式的全局快捷键功能需要管理员权限（Windows）或root权限（Linux）
2. **焦点问题**：使用时需要将焦点切换到目标应用（如游戏窗口），脚本会模拟键盘输入
3. **延迟调整**：根据实际情况调整各种间隔参数以达到最佳效果
4. **键位映射**：确保谱面文件中的字母与目标应用的键位对应

## 技术栈

- **Python 3.8+**
- **keyboard**: 原始键盘输入模拟（游戏输入，需要管理员权限）
- **pynput**: 文本输入模拟（备用方案）
- **tkinter**: 图形界面（Python内置）

**重要说明**：
- `keyboard` 库用于发送原始键盘按键事件，适合游戏和应用程序
- `pynput` 库用于文本输入，作为备用方案
- 推荐安装 `keyboard` 库以获得最佳效果
- Windows 上安装和运行 `keyboard` 库需要管理员权限

## 开发

本项目使用完整的类型注解，推荐使用支持类型检查的IDE（如PyCharm、VSCode）。

核心模块：
- `parser.py`: 使用递归下降解析器处理嵌套括号
- `player.py`: 多线程播放引擎，支持实时参数调整
- `keyboard_controller.py`: 封装pynput的键盘操作

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
