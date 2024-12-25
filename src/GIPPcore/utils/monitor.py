import keyboard

from threading import Thread


class Monitor(Thread):
    def __init__(self, conn, shortcut_key_manager):
        super().__init__()
        self.conn = conn
        self.shortcut_key_manager = shortcut_key_manager

    def run(self):
        while self.conn.running_flag:
            res_k = user_enter_monitor()
            if res_k is not None: res_k = res_k.lower()

            call_back = self.shortcut_key_manager.get_by_key(res_k)
            if call_back is not None: call_back(self.conn)

            self.check_event()

        self.conn.running_flag = False

    def check_event(self):
        if self.conn.modify_shortcut:
            self.conn.stop_flag = True
            self.conn.modify_shortcut = False
            self.shortcut_key_manager.modify_shortcut_key()

        if self.conn.save_shortcut:
            self.conn.save_shortcut = False
            self.shortcut_key_manager.generate_ini()


def user_enter_monitor():
    try:
        key_event = keyboard.read_event()
        if key_event.event_type == keyboard.KEY_DOWN:
            return key_event.name
    except KeyboardInterrupt:
        pass
