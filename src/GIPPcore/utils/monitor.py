from typing import TYPE_CHECKING, Optional, Union
import keyboard

from threading import Thread

if TYPE_CHECKING:
    from GIPPcore.ShortcutKeyManager import ShortcutKeyManager, ShortcutKey  # noqa
    from GIPPcore.Connection import Connection  # noqa

    SKMType = ShortcutKeyManager[Connection, Union[None, bool]]


class Monitor(Thread):

    def __init__(
            self,
            conn: 'Connection',
            shortcut_key_manager: 'SKMType',
    ):
        super().__init__()
        self.conn: 'Connection' = conn
        self.shortcut_key_manager: 'SKMType' = shortcut_key_manager

    def run(self):
        while self.conn.running_flag:
            res_k = user_enter_monitor()
            if res_k is not None:
                res_k = res_k.lower()

            call_back: Optional[ShortcutKey[Connection, Union[None, bool]]] = (
                self.shortcut_key_manager.get_by_key(str(res_k))
            )

            if call_back is not None and \
                    (not self.conn.keyboard_lock or call_back.is_always_active()):
                call_back(self.conn)

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
