from ..Config import Config


class Action:
    def __init__(self, cfg_str: str) -> None:
        self.is_valid: bool = ("=" in cfg_str)
        if not self.is_valid: return

        k, v = cfg_str.split("=")
        self.key: str = k.strip()
        self.value: float = float(v.strip())

        self.dispose_special()

    def __call__(self):
        setattr(Config, self.key, self.value)

    def dispose_special(self):
        if self.key == "SPEED":
            self.key = "PLAYER_INTERVAL"
            self.value = 1 / self.value

    def __str__(self) -> str:
        key = self.key
        if self.key == "PLAYER_INTERVAL":
            key = "SPEED"

        return f"$CFG[{key}={1 / self.value}]"

    def __repr__(self):
        return self.__str__()
