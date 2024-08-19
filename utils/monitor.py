import keyboard

from threading import Thread


class Monitor(Thread):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn

    def run(self):
        while self.conn.running_flag:
            res_k = user_enter_monitor()
            if res_k == "f1":
                self.conn.stop_flag = not self.conn.stop_flag
            elif res_k == "f2":
                self.conn.running_flag = False
            elif res_k == "f3":
                self.conn.restart = not self.conn.restart
            elif res_k == "f4":
                self.conn.reset_config = not self.conn.reset_config
            elif res_k == "f5":
                self.conn.hot_reload = not self.conn.hot_reload
                self.conn.running_flag = False
                break
            elif res_k == "up":
                self.conn.adjust_interval += 0.005
            elif res_k == "down":
                self.conn.adjust_interval -= 0.005
            elif res_k == "left":
                self.conn.adjust_progress -= 1
            elif res_k == "right":
                self.conn.adjust_progress += 1
            elif res_k == "p":
                self.conn.progress_adjust_rating = 2
            elif res_k == "o":
                self.conn.progress_adjust_rating = 0.5
            elif res_k == "i":
                self.conn.delay_press = not self.conn.delay_press
            elif res_k == "k":
                self.conn.adjust_space_interval -= 0.02
            elif res_k == "l":
                self.conn.adjust_space_interval += 0.02

        self.conn.running_flag = False


def user_enter_monitor():
    try:
        if (key_event := keyboard.read_event()).event_type == keyboard.KEY_DOWN:
            return key_event.name
    except KeyboardInterrupt:
        pass
