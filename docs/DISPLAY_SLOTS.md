# 显示插槽系统

GIPianoPlayer 使用插槽系统来组织 CLI 显示，避免硬编码的显示逻辑。

## 架构

### 核心组件

**DisplaySlotRegistry** - 显示插槽注册表
- 管理所有显示组件
- 支持优先级排序
- 提供渲染接口

**DisplayContext** - 显示上下文
- 提供当前状态信息
- 传递给渲染器

**DisplaySlot** - 显示插槽协议
- 定义渲染器接口

## 插槽类型

### 1. Header（头部）
- 应用标题
- 文件名
- 总行数

### 2. Score（乐谱）
- 乐谱内容
- 当前位置高亮
- 滚动指示器

### 3. Status（状态）
- 播放状态
- 当前位置
- 进度百分比

### 4. Config（配置）
- 速度设置
- 间隔设置
- 模式状态

### 5. Controls（控制）
- 快捷键提示
- 操作说明

## 使用方法

### 1. 注册渲染器

```python
from src.display_slots import get_display_slot_registry, DisplayContext

registry = get_display_slot_registry()

def my_renderer(context: DisplayContext) -> list[str]:
    """自定义渲染器"""
    return [
        f"Custom info: {context.current_line}",
        f"Width: {context.width}",
    ]

# 注册到 header 插槽
registry.register("header", my_renderer, priority=20)
```

### 2. 渲染插槽

```python
# 创建上下文
context = DisplayContext(
    player=player,
    score=score,
    current_line=10,
    current_note=5,
    total_lines=100,
    width=80,
    height=24,
)

# 渲染特定插槽
lines = registry.render_slot("header", context)
for line in lines:
    print(line)
```

### 3. 渲染所有插槽

```python
def render_display(context: DisplayContext) -> None:
    """渲染完整显示"""
    registry = get_display_slot_registry()

    # 按顺序渲染所有插槽
    for slot in ["header", "score", "status", "config", "controls"]:
        lines = registry.render_slot(slot, context)
        for line in lines:
            print(line)
```

## 优先级系统

渲染器按优先级排序（数字越小越先渲染）：

```python
# 优先级 10 - 最先渲染
registry.register("header", title_renderer, priority=10)

# 优先级 20 - 其次渲染
registry.register("header", subtitle_renderer, priority=20)

# 优先级 100 - 默认优先级
registry.register("header", info_renderer)
```

## DisplayContext 属性

```python
class DisplayContext:
    player: Any              # 播放器实例
    score: Any               # 解析的乐谱
    current_line: int        # 当前行号
    current_note: int        # 当前音符号
    total_lines: int         # 总行数
    width: int               # 终端宽度
    height: int              # 终端高度
    file_path: str           # 乐谱文件路径
```

## 在插件中使用

插件可以注册自定义显示组件：

```python
from src.plugin_system import Plugin, PluginContext
from src.display_slots import get_display_slot_registry, DisplayContext

class MyPlugin(Plugin):
    def initialize(self, context: PluginContext) -> None:
        # 注册显示组件
        registry = get_display_slot_registry()
        registry.register("status", self._render_my_status, priority=50)

    def _render_my_status(self, context: DisplayContext) -> list[str]:
        """渲染自定义状态"""
        return [
            f"Plugin Status: Active",
            f"Custom Info: {self._get_info()}",
        ]

    def cleanup(self) -> None:
        # 清理时注销
        registry = get_display_slot_registry()
        registry.unregister("status", self._render_my_status)
```

## 默认渲染器

### render_header()
```python
def render_header(context: DisplayContext, cli: CLI) -> list[str]:
    return [
        "GIPianoPlayer - Command Line Interface",
        "=" * 70,
        f"File: {os.path.basename(context.file_path)}",
        f"Lines: {len(context.score.lines)}",
        "",
    ]
```

### render_score()
```python
def render_score(context: DisplayContext, cli: CLI) -> list[str]:
    # 计算可见范围
    start_line = max(0, context.current_line - 3)
    end_line = min(len(context.score.lines), context.current_line + 7)

    # 渲染乐谱行
    lines = []
    for line_idx in range(start_line, end_line):
        line = context.score.lines[line_idx]
        line_text = cli._format_score_line(line)
        lines.append(f"{line_idx + 1:4d}. {line_text}")

    return lines
```

### render_status()
```python
def render_status(context: DisplayContext, cli: CLI) -> list[str]:
    state = context.player.get_state().value.upper()
    progress = calculate_progress(context)

    return [
        "",
        "=" * 70,
        f"Status: {state} | Line {context.current_line + 1}/{context.total_lines} | Progress: {progress:.1f}%",
        "",
    ]
```

### render_config()
```python
def render_config(context: DisplayContext, cli: CLI) -> list[str]:
    return [
        "Configuration",
        "-" * 70,
        f"  Speed: {context.player._speed_multiplier:.2f}x",
        f"  Arpeggio: {context.player._arpeggio_interval:.3f}s",
        # ... 更多配置项
        "",
    ]
```

### render_controls()
```python
def render_controls(context: DisplayContext, cli: CLI) -> list[str]:
    return [
        "Controls: [F8] Play/Pause | [F2] Quit | [F5] Reload",
        "          [←/→] Skip Note | [Ctrl+←/→] Skip Line",
        "",
    ]
```

## 自定义插槽

可以创建新的插槽类型：

```python
# 在初始化时添加新插槽
registry = get_display_slot_registry()
registry._slots["custom"] = []

# 注册渲染器
registry.register("custom", my_custom_renderer, priority=10)

# 渲染
lines = registry.render_slot("custom", context)
```

## 条件渲染

渲染器可以根据上下文条件返回内容：

```python
def conditional_renderer(context: DisplayContext) -> list[str]:
    """只在播放时显示"""
    if not context.player:
        return []

    if context.player.get_state() != PlayerState.PLAYING:
        return []

    return [
        "Currently playing...",
        f"Note: {context.current_note}",
    ]
```

## 错误处理

渲染器中的异常会被捕获：

```python
def buggy_renderer(context: DisplayContext) -> list[str]:
    # 如果出错，会显示错误信息而不是崩溃
    raise ValueError("Something went wrong")

# 输出: [Error rendering header: Something went wrong]
```

## 性能优化

### 1. 缓存计算结果

```python
class CachedRenderer:
    def __init__(self):
        self._cache = None
        self._last_line = -1

    def render(self, context: DisplayContext) -> list[str]:
        # 只在位置变化时重新计算
        if context.current_line != self._last_line:
            self._cache = self._compute_expensive_data(context)
            self._last_line = context.current_line

        return self._cache
```

### 2. 限制渲染频率

```python
import time

class ThrottledRenderer:
    def __init__(self):
        self._last_render = 0
        self._cached_result = []

    def render(self, context: DisplayContext) -> list[str]:
        now = time.time()
        if now - self._last_render < 0.1:  # 最多 10 FPS
            return self._cached_result

        self._cached_result = self._do_render(context)
        self._last_render = now
        return self._cached_result
```

## 与 CLI 集成

在 CLI 的 `_display_score` 方法中使用：

```python
def _display_score(self) -> None:
    """Display the full score using slot system."""
    if not self.display_active or not self.stdscr or not self.score:
        return

    # 创建上下文
    height, width = self.stdscr.getmaxyx()
    current_line, total_lines = self.player.get_progress() if self.player else (0, len(self.score.lines))
    current_note = self.player._current_note if self.player else 0

    context = DisplayContext(
        player=self.player,
        score=self.score,
        current_line=current_line,
        current_note=current_note,
        total_lines=total_lines,
        width=width,
        height=height,
        file_path=self.file_path,
    )

    # 渲染所有插槽
    registry = get_display_slot_registry()
    row = 0

    for slot in ["header", "score", "status", "config", "controls"]:
        lines = registry.render_slot(slot, context)
        for line in lines:
            if row < height - 1:
                self.stdscr.addstr(row, 0, line[:width-1])
                row += 1

    self.stdscr.refresh()
```

## 最佳实践

### 1. 保持渲染器简单
```python
# 好 - 简单直接
def simple_renderer(context: DisplayContext) -> list[str]:
    return [f"Line: {context.current_line}"]

# 不好 - 太复杂
def complex_renderer(context: DisplayContext) -> list[str]:
    # 100 行复杂逻辑...
    pass
```

### 2. 使用描述性的优先级
```python
# 好 - 清晰的优先级
PRIORITY_TITLE = 10
PRIORITY_SUBTITLE = 20
PRIORITY_CONTENT = 30

registry.register("header", title_renderer, PRIORITY_TITLE)
```

### 3. 处理边界情况
```python
def safe_renderer(context: DisplayContext) -> list[str]:
    if not context.score:
        return ["No score loaded"]

    if context.width < 40:
        return ["Terminal too narrow"]

    # 正常渲染
    return [...]
```

## 未来扩展

计划中的功能：
- [ ] 插槽布局配置（YAML/TOML）
- [ ] 动态插槽（运行时添加/删除）
- [ ] 插槽模板系统
- [ ] 主题支持（颜色方案）
- [ ] 响应式布局（根据终端大小调整）
