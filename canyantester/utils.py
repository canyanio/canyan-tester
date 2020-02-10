import os
import random
import struct


def generate_random_seed():
    return struct.unpack('I', os.urandom(4))[0]


def get_min_max_from_config(config, key, d=None):
    value = config.get(key)
    if value is None:
        value = d
    if isinstance(value, dict):
        value = (value.get('min'), value.get('max'))
    elif isinstance(value, int) or isinstance(value, float):
        value = (value, value)
    return value


def get_int_from_config(config, key, d=None):
    value = get_min_max_from_config(config, key)
    if value is None:
        return d
    return random.randint(*value)
