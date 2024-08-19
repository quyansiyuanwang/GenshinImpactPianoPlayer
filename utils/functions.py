from Consts import utils


def replace_all(text):
    for k, v in utils.REPLACE_MAP.items():
        text = text.replace(k, v)
    return text
