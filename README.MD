# 原神 凤物之诗琴 演奏器

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
    - `Left`: 快退
    - `Right`: 快进
    - `Up`: 加速
    - `Down`: 减速
    - `O`: 减少快进退的时间
    - `P`: 增加快进退的时间

## 文件配置说明
- 虽程序自带一些数据的初始化, 但是为了更好的演奏效果, 请自行在琴谱文件头进行配置
- 例如配置文件头部格式如下:
    ```txt
    0.75
    ARPEGGIO_INTERVAL=0.05
    INTERVAL_RATING=0.15
    SPACE_INTERVAL_RATING=0.65
    ------
    ```
- 配置项说明:
    - 第一行为数值, 为全局(琶音)弹琴速率(正相关)(无默认值)
    - ARPEGGIO_INTERVAL: 琶音的间隔时间, 默认为0.05
    - INTERVAL_RATING: 间隔时间的比例, 默认为0.15
    - SPACE_INTERVAL_RATING: 空格的比例, 默认为0.5
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