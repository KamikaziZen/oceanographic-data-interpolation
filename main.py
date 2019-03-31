"""
This is the example module.

This module does stuff.
"""

import matplotlib.pyplot as plt
import cartopy.crs as ccrs

import sys
import os
import argparse
from oceancolor import *
from utils import *
import pickle
import scipy
import time
import random
from datetime import datetime


def getopts():
    """Parse arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--config-path', type=str,
                        default='interpolate.conf')
    parser.add_argument('--config-set', type=str,
                        default='DEFAULT')
    return parser.parse_args()


if __name__ == '__main__':
    options = getopts()
    config = init_config(options.config_path, options.config_set)

    # checking list of chlor data files
    start_date = date2oceancolor_date(config['start_date'], config['date_format'])
    end_date = date2oceancolor_date(config['end_date'], config['date_format'])
    files = get_files(start_date, end_date, config['data_path'])
    if not files:
        print("no files with chlor data found for your search. try another time slice. ")
        sys.exit(1)

    # checking grid files for existance
    grid_exists = all([os.path.isfile('_lats.pkl'), os.path.isfile('_lons.pkl')])

    # confirmation
    print()
    print('CONFIGURATION FILE PATH: ', options.config_path)
    print('CONFIGURATION SET NAME: ', options.config_set)
    print('CHLOR DATA SOURCE: ', config['data_path'])
    print('SHAPE FILE: ', config['shape_file'])
    print()
    print('START DATE: ', config['start_date'])
    print('END DATE: ', config['end_date'])
    print()
    print('BOUNDARIES: ', ', '.join([config['min_lat'],
                                     config['max_lat'],
                                     config['min_lon'],
                                     config['max_lon']]))
    print()
    print('SPATIAL RESOLUTION: ', config['resolution'])
    print()
    print('GENERATING NEW INTERPOLATION GRID: ', not grid_exists)
    print()
    print(str(len(files)) + ' FILES HAVE BEEN FOUND FOR YOUR TIME SPECIFICATIONS')
    print()

    yes = ask_confirmation("Do you want to procede with these settings?")
    if not yes:
        sys.exit(0)

    # generate interpolation grid
    if not grid_exists:
        init_grid(config['shape_file'], float(config['resolution']))

    # load interpolation grid
    with open('_lons.pkl', 'rb') as f:
        _lons = pickle.load(f)
    with open('_lats.pkl', 'rb') as f:
        _lats = pickle.load(f)

    # crossval = []
    # day index for crossval points. valid cause file list is always sorted
    day = 0
    th = len(_lons.compressed()) * 0.05
    print("Threshold number of points: {}".format(th))

    start_time = time.time()
    outpath = datetime.now().strftime(config['config_prefix']+'_%Y-%m-%d_%H:%M:%S')
    # outpath = 'interpolated'
    os.makedirs(outpath)
    for fname in files:
        raw_lons, raw_lats, raw_ch_a = read_raw(os.path.join(config['data_path'], fname))
        if len(raw_ch_a.compressed()) < th:
            print('{} contains data for less then 5% of research area. '
                  'This document will not be used for interpolation.'.format(fname))
        else:
            ch_a = interpolate(raw_lons, raw_lats, raw_ch_a, _lons, _lats)
            if len(ch_a.compressed()) < th:
                print('{} contains data for less then 5% of research area. '
                      'This document will not be used for interpolation.'.format(fname))
                continue
            # jj, ii = np.meshgrid(range(ch_a.shape[1]), range(ch_a.shape[0]))
            # data_points = zip(ch_a.compressed(),
            #                   ma.array(ii, mask=ch_a.mask).compressed(),
            #                   ma.array(jj, mask=ch_a.mask).compressed())
            # print('setting aside {} points(3%) for cross-validation'.format(int(0.03 * len(ch_a.compressed()))))
            # for c, i, j in random.choices(list(data_points), k=int(0.03 * len(ch_a.compressed()))):
            #     crossval.append((i, j, day, c))
            day += 1

            fig = plt.figure(figsize=(10, 10))
            projection = ccrs.PlateCarree()
            ax = plt.axes(projection=projection)
            ax.contourf(_lons, _lats, ch_a)
            ax.set_extent([float(config['min_lat']),
                           float(config['max_lat']),
                           float(config['min_lon']),
                           float(config['max_lon'])], crs=projection)
            plt.savefig(os.path.join(outpath, fname.split('/')[-1].split('.')[0] + '.png'))
            plt.close('all')

            scipy.io.savemat(
                os.path.join(outpath, fname.split('.')[0]+'.mat'),
                {'chlor': ch_a.filled(fill_value=np.nan)}
            )

    print('--- %s seconds ---' % (time.time() - start_time))
    print(f'{day} files in {outpath}')
    # scipy.io.savemat('crossvalidation.mat', {'crossvalidation': crossval})
    # scipy.io.savemat('dineof_mask.mat', {'mask': ~_lons.mask * 1})
