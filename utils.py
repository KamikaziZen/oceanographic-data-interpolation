"""
Utils module
"""

import os
import fnmatch
from datetime import datetime
from configparser import RawConfigParser, NoSectionError, Error
import math


def init_config(config_path, config_set):
    """Initialize config"""
    parser = RawConfigParser()

    if not parser.read(config_path):
        raise Error('couldn\'t read ' + config_path)

    try:
        config = parser[config_set]
    except KeyError:
        raise NoSectionError('couldn\'t find ' + config_set + ' in ' + config_path)

    validate_config(config)

    return config


def validate_config(config):
    """Raise error if config doesn't pass validation"""
    required = {'date_format',
                'start_date',
                'end_date',
                'data_path',
                'variable_group',
                'variable',
                'shape_file',
                'resolution',
                'min_lat',
                'max_lat',
                'min_lon',
                'max_lon',
                'config_prefix'}

    if required - set(config.keys()) != set():
        raise Error('missing options. required: {}'.format(required))

    try:
        start_date = datetime.strptime(config['start_date'], config['date_format'])
    except Exception:
        raise ValueError('start_date do not correspond to date format')

    try:
        end_date = datetime.strptime(config['end_date'], config['date_format'])
    except Exception:
        raise ValueError('end_date do not correspond to date format')

    if end_date < start_date:
        raise ValueError('wrong time slice. end_date should be later than start_date')

    try:
        float(config['resolution'])
        float(config['min_lat'])
        float(config['max_lat'])
        float(config['min_lon'])
        float(config['max_lon'])
    except ValueError:
        raise ValueError('wrong value for resolution or bounds. expected int or float(dot format)')

    if not os.path.isfile(config['shape_file']):
        raise FileNotFoundError('shape file not found: ' + config['shape_file'] + ' does not exist')

    if not os.path.isdir(config['data_path']):
        raise FileNotFoundError('data path not found: ' + config['data_path'] + ' does not exist')


def ask_confirmation(question,):
    """"""
    print(question, '[y/n]')
    answer = input().lower()
    while answer not in ['y', 'yes', 'n', 'no']:
        print(question, '[y/n]')
        answer = input().lower()
    if answer in ('y', 'yes'):
        return True
    else:
        return False


def get_files(start_date, end_date, path):
    """Get list of files from date boundaries"""
    files = []
    for f in sorted(os.listdir(path)):
        if not fnmatch.fnmatch(f, '.*'):
            files.append(f)
    i1 = int(start_date)
    i2 = int(end_date)
    return [f for f in files if i1 <= int(f[1:8]) <= i2]


def custom_round(n):
    """"""
    if n == 0:
        return 0
    sgn = -1 if n < 0 else 1
    scale = int(-math.floor(math.log10(abs(n))))
    if scale <= 0:
        scale = 1
    factor = 10**scale
    return sgn*math.floor(abs(n)*factor)/factor
