# 配置优化建议

## 播放逻辑说明

### 核心规则

1. **每个音符之间都有间隔**
   - 单音符、和弦、琶音、空音（`/`）都算作一个音符
   - 每个音符后都会等待 INTERVAL_RATING 秒
   - 这样保证了节奏的一致性

2. **`/` 是空音**
   - 占据一个音符的位置
   - 不按任何键
   - 但会产生 INTERVAL_RATING 的间隔

3. **琶音的内部间隔**
   - 琶音内部的音符之间用 ARPEGGIO_INTERVAL 控制
   - 琶音作为整体后面还有 INTERVAL_RATING 间隔

### 示例

谱面：`(VAH) / H Q`

播放顺序：
1. 同时按下 V、A、H（和弦）
2. 等待 INTERVAL_RATING 秒
3. 空音（不按键）
4. 等待 INTERVAL_RATING 秒
5. 按下 H
6. 等待 INTERVAL_RATING 秒
7. 按下 Q

## 问题诊断

### 原配置（一笑江湖.qymusic）
```
INTERVAL_RATING=0.1
ARPEGGIO_INTERVAL=0.05
```

### 问题分析

**INTERVAL_RATING=0.1 秒太高**
- 每个音符后等待 0.1 秒（100 毫秒）
- 如果一行有 10 个音符，需要 1 秒
- 导致播放速度慢，不流畅

## 推荐配置

### 快速流畅（推荐）
```
1.4
ARPEGGIO_INTERVAL=0.02
INTERVAL_RATING=0.03
SPACE_INTERVAL_RATING=0
LINE_INTERVAL_RATING=0
------
```

### 中等速度
```
1.4
ARPEGGIO_INTERVAL=0.03
INTERVAL_RATING=0.05
SPACE_INTERVAL_RATING=0
LINE_INTERVAL_RATING=0
------
```

### 慢速练习
```
1.4
ARPEGGIO_INTERVAL=0.05
INTERVAL_RATING=0.08
SPACE_INTERVAL_RATING=0
LINE_INTERVAL_RATING=0
------
```

## 参数说明

### INTERVAL_RATING（音符间隔）
- **作用**：每个音符（单音、和弦、琶音、空音）之后的间隔
- **推荐值**：0.03-0.05 秒（快速）、0.05-0.08 秒（中速）
- **调整建议**：
  - 太小（<0.02）：可能按键丢失，游戏来不及响应
  - 太大（>0.1）：播放不流畅，节奏太慢
  - 根据游戏的响应速度调整

### ARPEGGIO_INTERVAL（琶音内部间隔）
- **作用**：琶音 `[ABC]` 中每个音符之间的间隔
- **推荐值**：0.02-0.03 秒
- **说明**：琶音是快速连续弹奏，所以间隔应该比普通音符小

### SPACE_INTERVAL_RATING（已废弃）
- 设置为 0 即可

### LINE_INTERVAL_RATING（换行间隔）
- **作用**：每行结束后的额外间隔
- **推荐值**：0（不使用）
- **使用场景**：如果乐曲需要在每行之间有明显停顿

## 实时调整

使用 GUI 模式可以实时调整参数：

```bash
uv run main.py --gui
```

1. 打开谱面文件
2. 点击 Play 开始播放
3. 使用滑块实时调整：
   - **Speed**：整体播放速度倍率（0.5x = 慢一半，2x = 快一倍）
   - **Arpeggio Interval**：琶音内部间隔
   - **Interval Rating**：可以通过修改配置文件调整

## 速度对比

### 原配置（INTERVAL_RATING=0.1）
- 10 个音符：1.0 秒
- 100 个音符：10 秒

### 优化后（INTERVAL_RATING=0.03）
- 10 个音符：0.3 秒
- 100 个音符：3 秒

**速度提升：3.3 倍！**

## 修改谱面文件

编辑你的 `.qymusic` 文件，将开头改为：

```
1.4
ARPEGGIO_INTERVAL=0.02
INTERVAL_RATING=0.03
SPACE_INTERVAL_RATING=0
LINE_INTERVAL_RATING=0
------
```

保存后重新加载即可。

## 调试技巧

如果播放还是不流畅：

1. **降低 INTERVAL_RATING**：从 0.03 降到 0.02
2. **使用 Speed 倍率**：在 GUI 中将 Speed 设置为 1.5x 或 2x
3. **检查游戏响应**：确保游戏窗口在前台，焦点正确
4. **测试按键**：打开记事本测试，确认按键输入正常

