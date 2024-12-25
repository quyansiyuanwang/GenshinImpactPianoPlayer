class Connection:
    def __init__(
            self, *,
            running_flag=True,
            stop_flag=True,
            delay_press=False,
            restart=False,
            reset_config=False,
            hot_reload=False,
            modify_shortcut=False,
            save_shortcut=False,
            progress_adjust_rating=1,
            adjust_interval=0,
            adjust_space_interval=0,
            adjust_progress=0
    ):
        self.running_flag = running_flag
        self.stop_flag = stop_flag
        self.delay_press = delay_press
        self.adjust_interval = adjust_interval
        self.adjust_space_interval = adjust_space_interval
        self.adjust_progress = adjust_progress
        self.progress_adjust_rating = progress_adjust_rating
        self.restart = restart
        self.reset_config = reset_config
        self.hot_reload = hot_reload
        self.modify_shortcut = modify_shortcut
        self.save_shortcut = save_shortcut
