from ..Config import Config


class Action:
    def __init__(self, cfg_str: str) -> None:
        self.is_valid: bool = ("=" in cfg_str)
        if not self.is_valid: return

        k, v = cfg_str.split("=")
        self.key: str = k.strip().lower()
        self.value: float = float(v.strip())

        self.dispose_special()

    def execute(self):
        print(self, end="")
        self.__call__()

    def __call__(self):
        setattr(Config, self.key, self.value)

    def dispose_special(self):
        if self.key == "speed":
            self.key = "player_interval"
            self.value = 1 / self.value

    def __str__(self) -> str:
        key = self.key
        value = self.value
        if self.key == "player_interval":
            key = "speed"
            value = 1 / self.value

        return f"$CFG[{key.upper()}={value}]"

    def __repr__(self):
        return self.__str__()
