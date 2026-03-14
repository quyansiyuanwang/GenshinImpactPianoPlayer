# 播放逻辑说明

## 当前实现的间隔逻辑

### 1. INTERVAL_RATING (基础间隔)
- 每个音符/和弦/琶音之后的间隔
- 当前：每个音符后 sleep(INTERVAL_RATING)

### 2. SPACE_INTERVAL_RATING (空格间隔)
- 遇到 `/` 符号时的额外间隔
- 当前：sleep(SPACE_INTERVAL_RATING * INTERVAL_RATING)

### 3. LINE_INTERVAL_RATING (换行间隔)
- 每行结束后的间隔
- 当前：sleep(LINE_INTERVAL_RATING * INTERVAL_RATING)

### 4. ARPEGGIO_INTERVAL (琶音间隔)
- 琶音中每个音符之间的间隔
- 当前：sleep(ARPEGGIO_INTERVAL)

## 问题分析

用户谱面配置：
- INTERVAL_RATING=0.1 (每个音符后 0.1 秒)
- SPACE_INTERVAL_RATING=1 (空格标记额外 0.1 秒)
- ARPEGGIO_INTERVAL=0.05 (琶音音符间 0.05 秒)

可能的问题：
1. 每个音符后都有 0.1 秒间隔可能太慢
2. 空格标记 `/` 已经是间隔标记，不应该再加基础间隔
3. 和弦和琶音后也加了间隔，可能不合理

## 建议的优化

1. 只在单音符后加 INTERVAL_RATING
2. 和弦和琶音本身已经有内部延迟，不需要额外间隔
3. 空格标记 `/` 只用 SPACE_INTERVAL_RATING，不叠加
