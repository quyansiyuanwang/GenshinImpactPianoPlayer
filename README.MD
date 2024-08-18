# 原神 凤物之诗琴 演奏器

## 语言 Language

- [English](Docs/README_EN.MD)
- [中文](README.MD)

## 介绍

这是一个原神的凤物之诗琴演奏器，可以通过简单的配置文件来演奏凤物之诗琴的曲子。

## 使用说明

1. 下载本项目
2. 安装依赖
    ```shell
    pip install -r requirements.txt
    ```
3. 配置文件
4. 将琴谱文件拖动到exe(需要管理员权限)上打开
5. 快捷键说明:
    - `F1`: 暂停/继续
    - `F2`: 退出
    - `F3`: 重新开始演奏
    - `F4`: 重新加载配置文件
    - `F5`: 重新加载琴谱文件
    - `Left`: 快退
    - `Right`: 增加演奏间隔
    - `Up`: 减少演奏间隔
    - `Down`: 减速
    - `O`: 减少快进退的时间
    - `P`: 增加快进退的时间
    - `I`: 切换模式(Piano/Horn)
    - `K`: 减少空音间隔倍率
    - `L`: 增加空音间隔倍率

## 文件配置说明

- 虽程序自带一些数据的初始化, 但是为了更好的演奏效果, 请自行在琴谱文件头进行配置
- 例如配置文件头部格式如下:
    ```txt
    0.75
    ARPEGGIO_INTERVAL=0.05
    INTERVAL_RATING=0.15
    SPACE_INTERVAL_RATING=0.5
    HORN_MODE_INTERVAL=0.01
    SPACE_FILLS=True
    LINE_INTERVAL_RATING=1
    IGNORE_BLANK_LINE=True
    ------
    ```
- 配置项说明:
    - 第一行为纯数值, 为全局(琶音)弹琴速率(正相关)(**无默认值**)
    - ARPEGGIO_INTERVAL: 琶音的间隔时间, 默认为`0.05`
    - INTERVAL_RATING: 间隔时间的比例, 默认为`0.15`
    - SPACE_INTERVAL_RATING: 空格的比例, 默认为`0.5`
    - HORN_MODE_INTERVAL: 圆号模式的自动休止间隔时间, 默认为`0.01`
    - SPACE_FILLS: 是否填充空格, 默认为真`True`
    - LINE_INTERVAL_RATING: 每行的间隔时间比例(需要为整数`int`), 默认为1
    - IGNORE_BLANK_LINE: 是否忽略空行, 默认为真`True`
    - 以 `-` 为开头的一行为分割行, 用于分割配置和琴谱

## 琴谱文件格式

- 琴谱文件为txt文件, 每行为一个音符, 例如:
    ```txt
    0.75
    ARPEGGIO_INTERVAL=0.05
    INTERVAL_RATING=0.15
    SPACE_INTERVAL_RATING=0.65
    ------
    (NAH)QHQ JD D D (VAH)QHQ JD D D
    (XNH)QHQ JD D D (CMH)QHQ JD D D
    (NAH)Q(NA)H(NAQ) JD D(NA) D
    (VAH)Q(VA)H(VAQ) JD D(VA) D
    (XNH)Q(XN)H(XNQ) JD D(XN) D
    (VAH)Q(VA)H(VAQ) (BSJ)D D(BS) D
    ```

- 圆号谱文件为txt文件, 例如:
    ```txt
    1.2
    ARPEGGIO_INTERVAL=0.05
    INTERVAL_RATING=0.15
    SPACE_INTERVAL_RATING=1
    HORN_MODE_INTERVAL=0.01
    ------
    (AQ)  E (GT)^ T (HY) ^ (GT) ^ /(DE)  Q (AT)^ T^ T (DE)  (AQ)  /
    (SG)^ G^ G^ (DG)^ G^ G (ADQ)   G /^(AQ) ^ (ADG) Q ^(AQ)  ^Q (FG) H J /
    (AQ) ^ (AGQ) ^ A E (ADQ) W E /(ST) ^ (AT) ^ (SE) ^ E (DQ) E /
    (AT)  E (HW) ^ (DW) ^ (DGT)^ T^ T /(NY)  (AGT) ^ (AW) ^ (ADE) ^ /
    (HT) E D T (AE)^ W E (GQ) A /(DE) ^ D ^ G  H (ADQ)^ Q^ /
    (GE)  ^E (GT)^ T (AW)^ W^ W (ADH) ^ /(AW) ^ (AD) G (AQ) ^ (AD)^ (AQ)^ /
    (AE) ^ (ADG) E (GT) ^ T^ T^ T /(AQ)  E (AGT)^ T (FY) ^ (AT) ^ /
    (AE)  Q (AGT)^ T^ T^ (AE) ^ (ADQ) ^ /(SG) ^ (AQ) ^ (AE)  Q (ADT)^ T^ T /
    (AE) ^ (ADQ) ^ (SG) ^ (AQ) ^ /(SG) ^ (AQ) ^ (SG) ^ (AQ) ^ /(AQ)    ^    /
    ```