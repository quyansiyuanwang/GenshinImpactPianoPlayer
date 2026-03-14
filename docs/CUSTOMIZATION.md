# 配置和快捷键自定义指南

## 新功能概述

### 1. 简化配置
- ✅ 删除了 `SPACE_INTERVAL_RATING`（空格现在是休止符）
- ✅ 删除了 `LINE_INTERVAL_RATING`（行间隔用空音表示）
- ✅ 只保留核心配置：
  - `ARPEGGIO_INTERVAL` - 琶音间隔
  - `INTERVAL_RATING` - 音符间隔

### 2. 快退/快进功能
- ✅ `←/→` - 跳过 1 行
- ✅ `Ctrl+←/→` - 跳过 10 行
- ✅ 可自定义跳过行数

### 3. 常量抽离
- ✅ 所有常量集中在 `src/constants.py`
- ✅ 易于修改和维护

### 4. 自定义快捷键
- ✅ 支持自定义所有快捷键
- ✅ 通过修改 `constants.py` 或传入参数

## 配置文件格式

### 新格式（简化）
```
1.4
ARPEGGIO_INTERVAL=0.02
INTERVAL_RATING=0.03
------

(VAH) _ _ _ H Q _ (BSJ) _ _ _ H G _
(CMG) _ S _ _ _ (CND) _ _ _ G D _
```

### 说明
- **ARPEGGIO_INTERVAL**: 琶音内部音符间隔（秒）
- **INTERVAL_RATING**: 每个音符之后的间隔（秒）
- **空音 `_`**: 用空格表示休止符
- **行间隔**: 在行尾添加空音来实现

## 自定义快捷键

### 方法 1: 修改 constants.py

编辑 `src/constants.py` 文件：

```python
DEFAULT_HOTKEYS = {
    # Playback control
    "play_pause": "space",    # 改为你想要的键
    "stop": "f8",             # 改为你想要的键
    "quit": "f2",             # 改为你想要的键

    # Speed adjustment
    "speed_up": "+",
    "speed_down": "-",

    # Arpeggio interval adjustment
    "arpeggio_faster": "[",
    "arpeggio_slower": "]",

    # Note interval adjustment
    "interval_shorter": ",",
    "interval_longer": ".",

    # Navigation
    "skip_backward": "left",
    "skip_forward": "right",
    "skip_backward_large": "ctrl+left",
    "skip_forward_large": "ctrl+right",
}
```

### 方法 2: 程序传入（高级）

```python
from src.cli import CLI

# 自定义快捷键
custom_hotkeys = {
    "play_pause": "p",
    "stop": "s",
    "quit": "q",
    # ... 其他快捷键
}

cli = CLI("score.qymusic", hotkeys=custom_hotkeys)
cli.run()
```

### 支持的按键格式

- 单键：`"a"`, `"1"`, `"space"`, `"enter"`
- 功能键：`"f1"`, `"f2"`, ..., `"f12"`
- 组合键：`"ctrl+c"`, `"alt+f4"`, `"shift+a"`
- 方向键：`"up"`, `"down"`, `"left"`, `"right"`

## 自定义常量

### 跳过行数

```python
# Skip amounts
SKIP_SMALL = 1   # 小跳：改为你想要的行数
SKIP_LARGE = 10  # 大跳：改为你想要的行数
```

### 调整步长

```python
# Adjustment steps
SPEED_STEP = 0.1          # 速度调整步长
ARPEGGIO_STEP = 0.01      # 琶音间隔调整步长
INTERVAL_STEP = 0.01      # 音符间隔调整步长
```

### 显示设置

```python
# Display settings
DISPLAY_REFRESH_RATE = 0.1  # 刷新频率（秒）
DISPLAY_LINES_BEFORE = 3    # 当前行前显示行数
DISPLAY_LINES_AFTER = 6     # 当前行后显示行数
```

### 播放限制

```python
# Playback limits
MIN_SPEED = 0.1
MAX_SPEED = 5.0
MIN_ARPEGGIO_INTERVAL = 0.01
MAX_ARPEGGIO_INTERVAL = 1.0
MIN_INTERVAL = 0.01
MAX_INTERVAL = 5.0
```

## 快捷键完整列表

### 播放控制
- `Space` - 播放/暂停
- `F8` - 停止
- `F2` - 退出

### 速度调整
- `+` - 加速（+0.1x）
- `-` - 减速（-0.1x）

### 间隔调整
- `[` - 琶音更快（-0.01s）
- `]` - 琶音更慢（+0.01s）
- `,` - 音符间隔更短（-0.01s）
- `.` - 音符间隔更长（+0.01s）

### 导航
- `←` - 后退 1 行
- `→` - 前进 1 行
- `Ctrl+←` - 后退 10 行
- `Ctrl+→` - 前进 10 行

## 使用示例

### 示例 1: 修改跳过行数

编辑 `src/constants.py`:
```python
SKIP_SMALL = 2   # 改为 2 行
SKIP_LARGE = 20  # 改为 20 行
```

现在：
- `←/→` 跳过 2 行
- `Ctrl+←/→` 跳过 20 行

### 示例 2: 修改快捷键

编辑 `src/constants.py`:
```python
DEFAULT_HOTKEYS = {
    "play_pause": "p",      # 改为 P 键
    "stop": "s",            # 改为 S 键
    "quit": "q",            # 改为 Q 键
    "skip_backward": "a",   # 改为 A 键
    "skip_forward": "d",    # 改为 D 键
    # ...
}
```

### 示例 3: 调整显示窗口

编辑 `src/constants.py`:
```python
DISPLAY_LINES_BEFORE = 5   # 前面显示 5 行
DISPLAY_LINES_AFTER = 10   # 后面显示 10 行
```

现在显示窗口更大，可以看到更多上下文。

### 示例 4: 调整刷新率

编辑 `src/constants.py`:
```python
DISPLAY_REFRESH_RATE = 0.05  # 20 FPS，更流畅但可能更闪烁
# 或
DISPLAY_REFRESH_RATE = 0.2   # 5 FPS，更稳定但不太流畅
```

## 配置迁移指南

### 旧配置
```
1.4
ARPEGGIO_INTERVAL=0.05
INTERVAL_RATING=0.1
SPACE_INTERVAL_RATING=1.0
LINE_INTERVAL_RATING=0.5
------
```

### 新配置
```
1.4
ARPEGGIO_INTERVAL=0.05
INTERVAL_RATING=0.1
------
```

### 迁移说明
1. 删除 `SPACE_INTERVAL_RATING`（不再需要）
2. 删除 `LINE_INTERVAL_RATING`（不再需要）
3. 如果需要行间隔，在行尾添加空音（空格）

## 总结

### 简化的配置
- ✅ 只有 2 个核心参数
- ✅ 更容易理解和调整
- ✅ 行间隔用空音表示，更灵活

### 强大的自定义
- ✅ 所有常量可自定义
- ✅ 所有快捷键可自定义
- ✅ 集中管理，易于维护

### 新增功能
- ✅ 快退/快进（1 行或 10 行）
- ✅ 可自定义跳过行数
- ✅ 更好的导航体验

祝你使用愉快！🎹
