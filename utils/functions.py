from Consts import utils


def replace_all(text):
    for k, v in utils.REPLACE_MAP.items():
        text = text.replace(k, v)
    return text


def reverse(tar, prop):
    if not hasattr(tar, prop): return False
    setattr(
        tar, prop,
        not getattr(tar, prop)
    )
    return True


def set_value(tar, prop, value):
    setattr(tar, prop, value)


def increase_value(tar, prop, value):
    if not hasattr(tar, prop): return False
    setattr(
        tar, prop,
        getattr(tar, prop) + value
    )
    return True
