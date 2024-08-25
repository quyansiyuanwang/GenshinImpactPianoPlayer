class Connection:
    running_flag: bool
    stop_flag: bool
    delay_press: bool
    restart: bool
    reset_config: bool
    hot_reload: bool
    modify_shortcut: bool
    save_shortcut: bool
    adjust_interval: float
    adjust_space_interval: float
    adjust_progress: int
    progress_adjust_rating: int

    def __init__(
            self, *,
            running_flag: bool = True,
            stop_flag: bool = True,
            delay_press: bool = False,
            restart: bool = False,
            reset_config: bool = False,
            hot_reload: bool = False,
            modify_shortcut: bool = False,
            save_shortcut: bool = False,
            progress_adjust_rating: int = 1,
            adjust_interval: float = 0,
            adjust_space_interval: float = 0,
            adjust_progress: int = 0
    ) -> None: ...
