class Connection:
    def __init__(
            self,
            *,
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
            adjust_progress: int = 0,
            keyboard_lock: bool = False,
    ) -> None:
        self.running_flag: bool = running_flag
        self.stop_flag: bool = stop_flag
        self.delay_press: bool = delay_press
        self.restart: bool = restart
        self.reset_config: bool = reset_config
        self.hot_reload: bool = hot_reload
        self.modify_shortcut: bool = modify_shortcut
        self.save_shortcut: bool = save_shortcut
        self.adjust_interval: float = adjust_interval
        self.adjust_space_interval: float = adjust_space_interval
        self.adjust_progress: int = adjust_progress
        self.progress_adjust_rating: int = progress_adjust_rating
        self.keyboard_lock: bool = keyboard_lock
