# CLI 统一输出接口说明

## 问题

在 CLI 模式中，如果有多个地方使用 `print()` 输出内容，会导致：
1. 光标位置混乱
2. 无法正确清除旧内容
3. 屏幕显示错乱

## 解决方案

### 统一输出接口

实现了三个核心方法：

#### 1. `_print()` - 普通输出
```python
def _print(self, *args, **kwargs):
    """Unified print interface - only use when display is not active."""
    if not self.display_active:
        print(*args, **kwargs)
```

**用途**：
- 初始化阶段的消息
- 错误消息
- 结束时的消息

**特点**：
- 只在 `display_active = False` 时工作
- 避免干扰显示模式

#### 2. `_output()` - 显示模式输出
```python
def _output(self, text: str):
    """Direct output for display mode."""
    sys.stdout.write(text)
    sys.stdout.flush()
```

**用途**：
- 显示模式下的所有输出
- 谱面显示
- 配置面板
- 状态信息

**特点**：
- 直接写入 stdout
- 立即刷新
- 完全控制输出

#### 3. `_clear_screen()` - 清屏
```python
def _clear_screen(self):
    """Clear the screen."""
    os.system('cls' if os.name == 'nt' else 'clear')
```

**用途**：
- 清除整个屏幕
- 准备输出新内容

**特点**：
- 使用系统命令
- 完全清除，不会遗漏
- 可靠性高

### 为什么使用清屏而不是光标移动？

#### 光标移动的问题
- ❌ 行数计算容易出错
- ❌ 动态内容（如配置调整）会改变行数
- ❌ 可能遗漏部分旧内容
- ❌ 调试困难

#### 清屏的优势
- ✅ 完全清除，不会遗漏
- ✅ 不需要追踪行数
- ✅ 简单可靠
- ✅ 易于维护

#### 闪烁控制
- 刷新频率：每 0.1 秒（10 FPS）
- 节流机制：避免过于频繁的刷新
- 可接受的闪烁：现代终端闪烁很轻微

### 状态追踪

```python
self.display_active = False      # 显示模式标志
self.last_display_time = 0       # 上次显示更新时间
```

## 使用规则

### ✅ 正确用法

```python
# 初始化阶段
self._print("Loading score...")

# 显示模式
self.display_active = True

# 清屏并输出
self._clear_screen()
self._output("Line 1\n")
self._output("Line 2\n")
self._output("Line 3\n")

# 结束阶段
self.display_active = False
self._print("Done!")
```

### ❌ 错误用法

```python
# 不要在显示模式中使用 print
self.display_active = True
print("This will break the display!")  # 错误！

# 不要直接使用 sys.stdout.write
sys.stdout.write("Direct output")  # 错误！应该用 _output()

# 不要直接调用 os.system('cls')
os.system('cls')  # 错误！应该用 _clear_screen()
```

## 完整工作流程

```python
def _display_score(self):
    # 1. 清屏
    self._clear_screen()

    # 2. 输出所有内容
    self._output("Header\n")
    self._output("Content\n")
    self._output("Footer\n")
```

## 节流机制

```python
def _on_progress(self, ...):
    current_time = time.time()
    # 只在距离上次刷新 >= 0.1 秒时才刷新
    if current_time - self.last_display_time >= 0.1:
        self._display_score()
        self.last_display_time = current_time
```

**优势**：
- 避免过于频繁的刷新
- 减少闪烁
- 降低 CPU 占用

## 工作流程图

```
初始化
  ↓
_print("Loading...")
  ↓
display_active = True
  ↓
┌─────────────────────┐
│  显示循环           │
│  ├─ _clear_screen() │
│  └─ _output(...)    │
└─────────────────────┘
  ↓
display_active = False
  ↓
_print("Finished!")
```

## 优势

### 1. 完全控制
- 所有输出都经过统一接口
- 没有意外输出
- 清晰的输出规则

### 2. 可靠性
- 清屏完全清除旧内容
- 不会遗漏任何行
- 不需要追踪行数

### 3. 易于维护
- 简单的实现
- 容易调试
- 便于扩展

### 4. 性能
- 节流机制控制刷新频率
- 10 FPS 足够流畅
- CPU 占用低

## 总结

统一输出接口的三个核心方法：

1. **`_print()`** - 普通输出（非显示模式）
2. **`_output()`** - 显示输出（显示模式）
3. **`_clear_screen()`** - 清屏（显示模式）

确保：
- ✅ 无意外输出
- ✅ 完全清除旧内容
- ✅ 可靠的显示更新
- ✅ 易于维护和调试

所有输出都必须通过这些接口进行！


#### 1. `_print()` - 普通输出
```python
def _print(self, *args, **kwargs):
    """Unified print interface - only use when display is not active."""
    if not self.display_active:
        print(*args, **kwargs)
```

**用途**：
- 初始化阶段的消息
- 错误消息
- 结束时的消息

**特点**：
- 只在 `display_active = False` 时工作
- 避免干扰显示模式

#### 2. `_output()` - 显示模式输出
```python
def _output(self, text: str):
    """Direct output for display mode - tracks output."""
    sys.stdout.write(text)
    sys.stdout.flush()
    self.output_buffer.append(text)
```

**用途**：
- 显示模式下的所有输出
- 谱面显示
- 配置面板
- 状态信息

**特点**：
- 直接写入 stdout
- 立即刷新
- 记录输出到 buffer
- 完全控制输出

#### 3. `_clear_output()` - 清除输出
```python
def _clear_output(self):
    """Clear previous output using cursor movement."""
    if self.last_output_lines > 0:
        # Move cursor up to the start
        sys.stdout.write(f'\033[{self.last_output_lines}A')
        # Clear from cursor to end of screen
        sys.stdout.write('\033[J')
        sys.stdout.flush()
```

**用途**：
- 清除上次的输出
- 准备输出新内容

**特点**：
- 使用 ANSI 转义序列
- 精确控制光标位置
- 不闪烁

#### 4. `_commit_output()` - 提交输出
```python
def _commit_output(self, num_lines: int):
    """Commit the current output and record line count."""
    self.last_output_lines = num_lines
    self.output_buffer.clear()
```

**用途**：
- 记录输出的行数
- 清空输出缓冲区
- 为下次更新做准备

**特点**：
- 记录行数用于下次清除
- 清空 buffer 释放内存

### 状态追踪

```python
self.display_active = False      # 显示模式标志
self.last_output_lines = 0       # 上次输出的行数
self.output_buffer = []          # 输出缓冲区
```

## 使用规则

### ✅ 正确用法

```python
# 初始化阶段
self._print("Loading score...")

# 显示模式
self.display_active = True

# 清除旧输出
self._clear_output()

# 输出新内容
self._output("Line 1\n")
self._output("Line 2\n")
self._output("Line 3\n")

# 提交输出
self._commit_output(3)  # 3 行

# 结束阶段
self.display_active = False
self._print("Done!")
```

### ❌ 错误用法

```python
# 不要在显示模式中使用 print
self.display_active = True
print("This will break the display!")  # 错误！

# 不要直接使用 sys.stdout.write
sys.stdout.write("Direct output")  # 错误！应该用 _output()

# 不要忘记 commit
self._output("Some text\n")
# 忘记调用 _commit_output()  # 错误！下次清除会失败
```

## 完整工作流程

```python
def _display_score(self):
    # 1. 清除旧输出
    self._clear_output()

    # 2. 构建新内容
    lines = []
    lines.append("Header")
    lines.append("Content")
    # ...

    # 3. 输出新内容
    for line in lines:
        self._output(line + '\n')

    # 4. 提交输出
    self._commit_output(len(lines))
```

## 工作流程图

```
初始化
  ↓
_print("Loading...")
  ↓
清屏 (os.system('cls'))
  ↓
display_active = True
  ↓
┌─────────────────────┐
│  显示循环           │
│  ├─ _clear_output() │
│  ├─ _output(...)    │
│  └─ _commit_output()│
└─────────────────────┘
  ↓
display_active = False
  ↓
_print("Finished!")
```

## 优势

### 1. 完全控制
- 所有输出都经过统一接口
- 没有意外输出
- 准确追踪行数和内容

### 2. 无闪烁
- 使用光标移动技术
- 准确清除旧内容
- 流畅的视觉体验

### 3. 易于维护
- 清晰的输出规则
- 容易调试
- 便于扩展

### 4. 内存管理
- output_buffer 追踪输出
- commit 后清空 buffer
- 避免内存泄漏

## 实现细节

### 光标控制

```python
# 向上移动 N 行
sys.stdout.write(f'\033[{N}A')

# 清除光标到屏幕底部
sys.stdout.write('\033[J')

# 回到行首
sys.stdout.write('\r')

# 换行
sys.stdout.write('\n')
```

### 行数计算

```python
lines = []
lines.append("Line 1")
lines.append("Line 2")
# ...

num_lines = len(lines)  # 准确的行数
self._commit_output(num_lines)
```

### Buffer 管理

```python
# 输出时添加到 buffer
def _output(self, text: str):
    sys.stdout.write(text)
    sys.stdout.flush()
    self.output_buffer.append(text)  # 记录

# 提交时清空 buffer
def _commit_output(self, num_lines: int):
    self.last_output_lines = num_lines
    self.output_buffer.clear()  # 清空
```

## 调试技巧

### 1. 检查输出模式

```python
if self.display_active:
    print("Display mode is active")  # 这会破坏显示
else:
    print("Safe to print")  # 安全
```

### 2. 追踪行数

```python
print(f"Last output lines: {self.last_output_lines}")
print(f"Buffer size: {len(self.output_buffer)}")
```

### 3. 验证清除

```python
def _clear_output(self):
    if self.last_output_lines > 0:
        print(f"Clearing {self.last_output_lines} lines")  # 调试
        sys.stdout.write(f'\033[{self.last_output_lines}A')
        sys.stdout.write('\033[J')
```

## 测试

### 单元测试

```python
def test_output_interface():
    cli = CLI("test.txt")

    # 测试初始状态
    assert cli.display_active == False
    assert cli.last_output_lines == 0
    assert len(cli.output_buffer) == 0

    # 测试显示模式
    cli.display_active = True
    cli._output("Test\n")
    assert len(cli.output_buffer) == 1

    # 测试提交
    cli._commit_output(1)
    assert cli.last_output_lines == 1
    assert len(cli.output_buffer) == 0
```

## 总结

统一输出接口的四个核心方法：

1. **`_print()`** - 普通输出（非显示模式）
2. **`_output()`** - 显示输出（记录到 buffer）
3. **`_clear_output()`** - 清除旧输出（使用光标移动）
4. **`_commit_output()`** - 提交输出（记录行数，清空 buffer）

确保：
- ✅ 无意外输出
- ✅ 准确的光标控制
- ✅ 流畅的显示更新
- ✅ 完整的状态追踪
- ✅ 易于维护和调试

所有输出都必须通过这些接口进行！


## 使用规则

### ✅ 正确用法

```python
# 初始化阶段
self._print("Loading score...")

# 显示模式
self.display_active = True
self._output("Score content\n")

# 结束阶段
self.display_active = False
self._print("Done!")
```

### ❌ 错误用法

```python
# 不要在显示模式中使用 print
self.display_active = True
print("This will break the display!")  # 错误！

# 不要直接使用 sys.stdout.write
sys.stdout.write("Direct output")  # 错误！应该用 _output()
```

## 工作流程

```
1. 初始化
   ├─ _print("Loading...")
   └─ 解析谱面

2. 清屏
   └─ os.system('cls')

3. 启动显示模式
   ├─ display_active = True
   ├─ _display_score()  # 使用 _output()
   └─ _output("Starting in 3s\n")

4. 播放循环
   └─ _display_score()  # 持续使用 _output()

5. 结束
   ├─ display_active = False
   └─ _print("Finished!")
```

## 优势

### 1. 输出控制
- 所有输出都经过统一接口
- 可以追踪输出的行数
- 准确清除旧内容

### 2. 状态管理
- `display_active` 标志控制输出模式
- 避免意外输出干扰显示

### 3. 调试友好
- 容易找到所有输出点
- 可以添加日志记录
- 便于排查问题

## 实现细节

### 行数追踪

```python
self.last_output_lines = 0  # 追踪上次输出的行数

def _display_score(self):
    lines = []
    # ... 构建输出 ...

    num_lines = len(lines)

    # 清除旧内容
    if self.last_output_lines > 0:
        self._output(f'\033[{self.last_output_lines}A')  # 上移
        self._output('\033[J')  # 清除

    # 输出新内容
    for line in lines:
        self._output(line + '\n')

    # 记录行数
    self.last_output_lines = num_lines
```

### 光标控制

- `\033[NA` - 向上移动 N 行
- `\033[J` - 清除光标到屏幕底部
- `\r` - 回到行首
- `\n` - 换行

## 测试

### 验证输出控制

```python
# 测试 1: 初始化输出
cli = CLI("test.txt")
# 应该看到警告消息

# 测试 2: 显示模式
cli.display_active = True
cli._print("This should not appear")  # 不会输出
cli._output("This will appear\n")     # 会输出

# 测试 3: 结束输出
cli.display_active = False
cli._print("This will appear")  # 会输出
```

## 总结

统一输出接口确保：
- ✅ 无意外输出
- ✅ 准确的光标控制
- ✅ 流畅的显示更新
- ✅ 易于维护和调试

所有输出都必须通过 `_print()` 或 `_output()` 进行！
