# Genshin Impact Phoenix Monogram Poetry Piano Player

## 语言 Language

- [English](README_EN.MD)
- [中文](../README.MD)

## Introduction

This is a Genshin Impact's Phoenix Poetry Piano Player that can play the tunes of the Phoenix Mono Poetry Piano with a
simple profile.

## Instructions for use

1. Download the project
2. Install dependencies
    ```shell
    pip install -r requirements.txt
    ```
3. Configuration Files
4. Drag the score file onto the exe (administrator privileges required) to open it
5. Default shortcut description:
    - `F1`: Pause/resume
    - `F2`: Exit
    - `F3`: Start playing again
    - `F4`: Reload the configuration file
    - `F5`: Reload the score file
    - `F6`: Modify the shortcut settings
    - `F7`: Saves the current shortcut settings
    - `Left`: Rewind
    - `Right`: Increase the interval between performances
    - `Up`: Reduce the interval between plays
    - `Down`: Slows down
    - `O`: Reduces the time it takes to fast-forward and rewind
    - `P`: Increases the time to fast-forward and rewind
    - `I`: Switch mode (Piano/Horn)
    - `K`: Reduced air interval magnification
    - `L`: Increases the multiplier of the interval between air tones
6. Configure shortcuts through configuration files
    - The configuration file is`~/keysConfig/keyMap.ini`
    - The default configuration file format is as follows:
        ```ini
        start/stop=f1
        exit=f2
        restart=f3
        reset config=f4
        hotreload music=f5
        increase interval=up
        decrease interval=down
        go back=left
        go forward=right
        double progress=p
        halve progress=o
        switch mode=i
        increase space interval=k
        decrease space interval=l
        save shortcut=f7
        ```
    - If you need to modify the shortcut key, please modify the corresponding content, or enter the program to modify
    - If there is no profile, a default profile is automatically generated
    - Note that the key value of the shortcut key needs to be lowercase, and there must be no modifier keys such as 
`ctrl` or `alt`

## File configuration description

- Although the program comes with some data initialization, in order to play better, please configure it in the score
  file header
- For example, the configuration file header format is as follows:
    ```txt
    0.75
    ARPEGGIO_INTERVAL=0.05
    INTERVAL_RATING=0.15
    SPACE_INTERVAL_RATING=0.65
    SPACE_INTERVAL_RATING=0.5
    HORN_MODE_INTERVAL=0.01
    SPACE_FILLS=True
    LINE_INTERVAL_RATING=1
    IGNORE_BLANK_LINE=True
    ------
    ```
- Description:
    - The first line is a numeric value, which is the global (arpeggio) playing rate (positive correlation) (**no default
      value**)
    - ARPEGGIO_INTERVAL: The interval between arpeggios, default is `0.05`
    - INTERVAL_RATING: The ratio of the interval, default is `0.15`
    - SPACE_INTERVAL_RATING: The scale of the space, which is `0.5` by default
    - HORN_MODE_INTERVAL: The automatic rest interval of the horn mode, default is `0.01`
    - SPACE_FILLS: Whether to fill in the space, default is 'True'
    - LINE_INTERVAL_RATING: The interval timescale for each row (needs to be an integer 'int'), defaults to `0`
    - IGNORE_BLANK_LINE: Whether to ignore blank lines, default is 'True'
    - A line that starts with '-' splits the line to split the configuration and score

## Sheet music file format

- The score file is a txt file, one note per line, for example:
    ```txt
    0.75
    ARPEGGIO_INTERVAL=0.05
    INTERVAL_RATING=0.15
    SPACE_INTERVAL_RATING=0.65
    ------
    (NAH) QHQ JD D D (VAH)QHQ JD D D
    (XNH) QHQ JD D D (CMH)QHQ JD D D
    (NAH) Q(NA)H(NAQ) JD D(NA) D
    (VAH) Q(VA)H(VAQ) JD D(VA) D
    (XNH) Q(XN)H(XNQ) JD D(XN) D
    (VAH) Q(VA)H(VAQ) (BSJ)D D(BS) D
    ```

- Horn staff files are txt files, for example:
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