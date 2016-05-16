def get_val_from_const(value, constants, chan=None):
    if value is None:
        return None
    elif isinstance(value, basestring):
        if chan and isinstance(constants[value], dict) and chan in constants[value]:
            return constants[value][chan]
        else:
            return constants[value]
    else:
        return value


def cap(value):
    if value > 255:
        value = 255
    if value < 0:
        value = 0
    return int(value)
