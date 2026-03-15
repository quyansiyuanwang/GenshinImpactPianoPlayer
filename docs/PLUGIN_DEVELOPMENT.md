# 插件开发指南

GIPianoPlayer 提供了一个灵活的插件系统，允许你扩展播放器的功能。

## 插件系统架构

### 核心组件

1. **Plugin** - 插件基类
2. **PluginContext** - 插件上下文，提供对核心组件的访问
3. **PluginManager** - 插件管理器，负责加载和管理插件

### 插件生命周期

```
加载 → 初始化 → 启用 → 运行 → 禁用 → 清理
```

## 创建插件

### 1. 基本插件结构

```python
from src.plugin_system import Plugin, PluginContext

class MyPlugin(Plugin):
    def __init__(self) -> None:
        super().__init__("my_plugin", "1.0.0")
        # 初始化插件状态

    def initialize(self, context: PluginContext) -> None:
        """插件初始化，注册热键和回调"""
        # 注册自定义热键
        context.register_hotkey("ctrl+p", self._my_action)

    def _my_action(self) -> None:
        """热键回调函数"""
        if not self.enabled:
            return
        # 执行操作

    def cleanup(self) -> None:
        """清理资源"""
        # 释放资源
```

### 2. 访问核心组件

通过 `PluginContext` 访问：

```python
def initialize(self, context: PluginContext) -> None:
    # 访问播放器
    self.player = context.player

    # 访问 CLI
    self.cli = context.cli

    # 访问配置
    self.config = context.config
```

### 3. 注册热键

```python
# 单个热键
context.register_hotkey("f10", self._toggle_feature)

# 组合键
context.register_hotkey("ctrl+shift+s", self._save_state)

# 多个热键
for i in range(1, 10):
    context.register_hotkey(f"ctrl+{i}", lambda n=i: self._action(n))
```

## 内置插件示例

### SpeedControlPlugin - 速度控制

提供速度预设功能：

- `Ctrl+Shift+Up` - 下一个速度预设
- `Ctrl+Shift+Down` - 上一个速度预设
- `Ctrl+0` - 重置速度到 1.0x

### LoopPlugin - 循环播放

提供区间循环功能：

- `Ctrl+[` - 设置循环起点
- `Ctrl+]` - 设置循环终点
- `Ctrl+L` - 开关循环
- `Ctrl+Shift+L` - 清除循环点

### MetronomePlugin - 节拍器

提供节拍器功能：

- `Ctrl+M` - 开关节拍器
- `Ctrl+Shift+,` - 降低 BPM
- `Ctrl+Shift+.` - 提高 BPM

### BookmarkPlugin - 书签

提供位置书签功能：

- `Ctrl+1-9` - 设置书签
- `Alt+1-9` - 跳转到书签

## 插件配置

在 `plugins.toml` 中配置插件：

```toml
[plugins]
enabled = [
    "speed_control",
    "loop",
    "my_custom_plugin",
]

[plugins.my_custom_plugin]
setting1 = "value1"
setting2 = 42
```

## 加载自定义插件

### 方法 1：放在 src/plugins/ 目录

```python
# src/plugins/my_plugin.py
from src.plugin_system import Plugin, PluginContext

class MyCustomPlugin(Plugin):
    def __init__(self) -> None:
        super().__init__("my_custom", "1.0.0")

    def initialize(self, context: PluginContext) -> None:
        # 实现插件逻辑
        pass
```

### 方法 2：外部插件目录

1. 在 `plugins.toml` 中添加路径：

```toml
[plugins.custom_paths]
paths = [
    "path/to/my/plugins",
]
```

2. 创建插件文件：

```python
# path/to/my/plugins/my_plugin.py
from src.plugin_system import Plugin, PluginContext

class Plugin:  # 必须命名为 Plugin
    def __init__(self) -> None:
        super().__init__("external_plugin", "1.0.0")
```

## 插件 API 参考

### Plugin 基类

```python
class Plugin(ABC):
    name: str                    # 插件名称
    version: str                 # 插件版本
    enabled: bool                # 是否启用

    def initialize(context)      # 初始化插件
    def cleanup()                # 清理资源
    def on_enable()              # 启用时调用
    def on_disable()             # 禁用时调用
```

### PluginContext

```python
class PluginContext:
    player: Player               # 播放器实例
    cli: CLI                     # CLI 实例
    config: dict                 # 配置字典

    def register_hotkey(key, callback)  # 注册热键
    def get_hotkeys()                   # 获取所有热键
```

### PluginManager

```python
manager = get_plugin_manager()

manager.register_plugin(plugin)      # 注册插件
manager.unregister_plugin(name)      # 注销插件
manager.get_plugin(name)             # 获取插件
manager.enable_plugin(name)          # 启用插件
manager.disable_plugin(name)         # 禁用插件
```

## 最佳实践

### 1. 错误处理

```python
def _my_action(self) -> None:
    if not self.enabled:
        return

    try:
        # 执行操作
        pass
    except Exception as e:
        print(f"Plugin error: {e}")
```

### 2. 状态管理

```python
class MyPlugin(Plugin):
    def __init__(self) -> None:
        super().__init__("my_plugin", "1.0.0")
        self._state = {}

    def cleanup(self) -> None:
        # 保存状态
        self._save_state()
```

### 3. 性能考虑

- 避免在热键回调中执行耗时操作
- 使用异步操作处理长时间任务
- 及时释放不需要的资源

### 4. 兼容性

- 检查核心组件是否存在
- 提供降级方案
- 文档化依赖关系

## 调试插件

### 启用调试输出

```python
def initialize(self, context: PluginContext) -> None:
    print(f"[{self.name}] Initializing...")
    print(f"[{self.name}] Player: {context.player}")
    print(f"[{self.name}] CLI: {context.cli}")
```

### 测试插件

```python
# test_my_plugin.py
from src.plugin_system import PluginContext
from src.plugins.my_plugin import MyPlugin

def test_plugin():
    plugin = MyPlugin()
    context = PluginContext()
    plugin.initialize(context)

    # 测试功能
    plugin._my_action()
```

## 示例：完整的自定义插件

```python
from src.plugin_system import Plugin, PluginContext

class RecordingPlugin(Plugin):
    """录制播放操作的插件"""

    def __init__(self) -> None:
        super().__init__("recording", "1.0.0")
        self._recording = False
        self._actions = []

    def initialize(self, context: PluginContext) -> None:
        self.player = context.player

        # 注册热键
        context.register_hotkey("ctrl+r", self._toggle_recording)
        context.register_hotkey("ctrl+shift+r", self._replay)

    def _toggle_recording(self) -> None:
        """开关录制"""
        if not self.enabled:
            return

        self._recording = not self._recording
        if self._recording:
            self._actions = []
            print("🔴 Recording started")
        else:
            print(f"⏹️  Recording stopped ({len(self._actions)} actions)")

    def _replay(self) -> None:
        """回放录制的操作"""
        if not self.enabled or not self._actions:
            return

        print(f"▶️  Replaying {len(self._actions)} actions...")
        for action in self._actions:
            # 执行录制的操作
            pass

    def cleanup(self) -> None:
        """清理资源"""
        self._actions.clear()
```

## 发布插件

### 1. 打包插件

```
my_plugin/
├── __init__.py
├── plugin.py
├── README.md
└── requirements.txt
```

### 2. 文档化

- 功能说明
- 热键列表
- 配置选项
- 依赖要求

### 3. 分享

- 发布到 GitHub
- 提交到插件仓库
- 编写使用教程

## 更多资源

- [插件系统源码](../src/plugin_system.py)
- [内置插件示例](../src/plugins/)
- [插件配置](../plugins.toml)
