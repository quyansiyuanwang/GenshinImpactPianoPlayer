# 热键注册系统

GIPianoPlayer 使用集中式的热键注册系统，方便管理和扩展热键功能。

## 架构

### 核心组件

**HotkeyRegistry** - 热键注册表
- 集中管理所有热键
- 支持分类和描述
- 提供查询和管理接口

**register_default_hotkeys()** - 注册默认热键
- 在 `src/default_hotkeys.py` 中定义
- 注册所有内置热键

## 使用方法

### 1. 注册热键

```python
from src.hotkey_registry import get_hotkey_registry

registry = get_hotkey_registry()

# 注册单个热键
registry.register(
    key="ctrl+p",           # 热键组合
    callback=my_function,   # 回调函数
    description="暂停播放",  # 描述
    category="playback"     # 分类
)
```

### 2. 查询热键

```python
# 获取所有热键
all_hotkeys = registry.get_all_hotkeys()

# 获取特定分类的热键
playback_hotkeys = registry.get_by_category("playback")

# 获取热键描述
desc = registry.get_description("ctrl+p")
```

### 3. 注销热键

```python
registry.unregister("ctrl+p")
```

## 默认热键分类

### Playback（播放控制）
- `F8` - 播放/暂停
- `F2` - 退出

### Speed（速度控制）
- `+` - 增加速度（小）
- `-` - 减少速度（小）
- `Ctrl+=` - 增加速度（大）
- `Ctrl+_` - 减少速度（大）

### Timing（时间控制）
- `[` - 加快琶音
- `]` - 减慢琶音
- `,` - 减少音符间隔
- `.` - 增加音符间隔
- `↑` - 增加行间隔
- `↓` - 减少行间隔
- `Shift+↑` - 增加空格间隔
- `Shift+↓` - 减少空格间隔
- `Ctrl+↑` - 增加空行间隔
- `Ctrl+↓` - 减少空行间隔

### Segment（段落控制）
- `Page Up` - 增加段落长度
- `Page Down` - 减少段落长度

### Navigation（导航）
- `←` - 后退 1 音符
- `→` - 前进 1 音符
- `Ctrl+←` - 后退 1 行
- `Ctrl+→` - 前进 1 行

### File（文件操作）
- `F5` - 重新加载文件
- `F6` - 重新解析
- `F9` - 保存配置

### Mode（模式切换）
- `F7` - 切换延音模式
- `F4` - 切换严格段落模式

## 在插件中使用

插件可以通过 `PluginContext` 注册自定义热键：

```python
from src.plugin_system import Plugin, PluginContext

class MyPlugin(Plugin):
    def initialize(self, context: PluginContext) -> None:
        # 通过 context 注册热键
        context.register_hotkey("ctrl+p", self._my_action)

        # 或直接使用 registry
        from src.hotkey_registry import get_hotkey_registry
        registry = get_hotkey_registry()
        registry.register(
            "ctrl+shift+p",
            self._another_action,
            "My custom action",
            "custom"
        )
```

## 热键命名规范

### 修饰键
- `ctrl` - Ctrl 键
- `shift` - Shift 键
- `alt` - Alt 键

### 组合方式
- 使用 `+` 连接：`ctrl+shift+p`
- 小写字母：`ctrl+a`
- 功能键：`f1`, `f2`, ...
- 特殊键：`up`, `down`, `left`, `right`, `page up`, `page down`

### 示例
```python
"ctrl+p"          # Ctrl + P
"shift+up"        # Shift + 上箭头
"ctrl+shift+s"    # Ctrl + Shift + S
"f10"             # F10
"page down"       # Page Down
```

## 热键冲突处理

注册系统会自动检测冲突：

```python
registry.register("ctrl+p", func1, "Action 1")
registry.register("ctrl+p", func2, "Action 2")  # 抛出 ValueError
```

解决方案：
1. 使用不同的热键
2. 先注销旧热键：`registry.unregister("ctrl+p")`
3. 使用插件系统的优先级机制

## 查看所有热键

```python
from src.hotkey_registry import get_hotkey_registry

registry = get_hotkey_registry()

# 按分类显示
for category in registry.get_all_categories():
    print(f"\n{category.upper()}:")
    for key, desc in registry.get_by_category(category):
        print(f"  {key:20s} - {desc}")
```

输出示例：
```
PLAYBACK:
  f8                   - Play/Pause playback
  f2                   - Quit application

SPEED:
  +                    - Increase speed (small)
  -                    - Decrease speed (small)
  ...
```

## 最佳实践

### 1. 使用描述性的分类名
```python
# 好
registry.register("ctrl+p", func, "Pause", "playback")

# 不好
registry.register("ctrl+p", func, "Pause", "misc")
```

### 2. 提供清晰的描述
```python
# 好
"Increase playback speed by 0.1x"

# 不好
"Speed up"
```

### 3. 避免常用热键冲突
避免使用：
- `Ctrl+C` (复制/中断)
- `Ctrl+V` (粘贴)
- `Ctrl+Z` (撤销)
- `Ctrl+S` (保存)

### 4. 使用一致的命名
```python
# 好 - 一致的模式
"ctrl+up"    # 增加
"ctrl+down"  # 减少

# 不好 - 不一致
"ctrl+up"    # 增加
"ctrl+d"     # 减少
```

## 与 CLI 集成

在 CLI 中使用热键注册系统：

```python
def _setup_hotkeys(self) -> None:
    """Setup keyboard shortcuts using hotkey registry."""
    if keyboard is None:
        return

    # 注册默认热键
    from src.default_hotkeys import register_default_hotkeys
    from src.hotkey_registry import get_hotkey_registry

    register_default_hotkeys(self)

    # 绑定到 keyboard 库
    registry = get_hotkey_registry()
    for key, callback in registry.get_all_hotkeys().items():
        keyboard.add_hotkey(key, callback)
```

## 动态热键管理

### 运行时添加热键
```python
def add_custom_hotkey(key: str, action: Callable) -> None:
    registry = get_hotkey_registry()
    registry.register(key, action, "Custom action", "custom")

    # 如果 keyboard 已初始化，立即绑定
    if keyboard:
        keyboard.add_hotkey(key, action)
```

### 运行时移除热键
```python
def remove_hotkey(key: str) -> None:
    registry = get_hotkey_registry()
    registry.unregister(key)

    # 从 keyboard 库移除
    if keyboard:
        keyboard.remove_hotkey(key)
```

## 未来扩展

计划中的功能：
- [ ] 热键配置文件（hotkeys.toml）
- [ ] 用户自定义热键映射
- [ ] 热键冲突自动解决
- [ ] 热键帮助界面（显示所有可用热键）
- [ ] 热键录制功能
