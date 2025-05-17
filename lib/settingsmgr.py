from .plato import appdata_path
from json   import load, dump
from os     import makedirs

APPDATA_PATH = appdata_path('BubblesAndChillout')

default_settings = {
    'locale': 0,
    'shuffle': True,
    'shake_level': 1
}
try:
    makedirs(f'{APPDATA_PATH}/')
    settings = default_settings
    with open(f'{APPDATA_PATH}/settings.json', 'w') as file:
        dump(default_settings, file)
except OSError:
    with open(f'{APPDATA_PATH}/settings.json', 'r') as file:
        settings = load(file)
    if settings.keys() != default_settings.keys():
        settings = default_settings
        with open(f'{APPDATA_PATH}/settings.json', 'w') as file:
            dump(default_settings, file)

def save_settings():
    with open(f'{APPDATA_PATH}/settings.json', 'w') as file:
        dump(settings, file)