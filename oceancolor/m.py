"""
This is a module for working with oceancolor data.
"""

import sys
from datetime import datetime
import geopandas
import netCDF4 as nc
from shapely.geometry import MultiPoint, Point
import numpy as np
import numpy.ma as ma
import pickle
from scipy.spatial.distance import euclidean
from sklearn import neighbors
import calendar
from utils import *


def oceancolor_date2date(oc_date : str) -> datetime.date:
    """"""
    year = int(oc_date[:4])
    daynum = int(oc_date[4:])
    month = 1
    day = daynum
    while month < 13:
        month_days = calendar.monthrange(year, month)[1]
        if day <= month_days:
            return datetime.date(year, month, day)
        day -= month_days
        month += 1
    raise ValueError('{} does not have {} days'.format(year, daynum))


def date2oceancolor_date(datestring, dateformat):
    """Format date with dateformat into YYYYDDD format
    """
    d = datetime.strptime(datestring, dateformat)
    d0 = datetime(d.year, 1, 1, 0, 0)
    # days since start of the year
    days = (d-d0).days + 1
    return str(d.year) + '%03d' % days


def init_grid(shape_file, resolution):
    """Generate spatial grid
    :param shape_file: shape file of the lake
    """
    data = geopandas.GeoSeries.from_file(shape_file)
    lake = data[0]
    lon1, lat1, lon2, lat2 = lake.bounds

    # 111 and 65 are approximate number of kilometers per 1 degree of latitude and longitude accordingly
    spar_lat = abs(int((lat2 - lat1) * 111 / resolution))
    spar_lon = abs(int((lon2 - lon1) * 65 / resolution))
    print('Grid shape: {}x{}'.format(spar_lat, spar_lon))

    lons, lats = np.meshgrid(np.linspace(lon1, lon2, spar_lon), np.linspace(lat2, lat1, spar_lat))
    grid = list(zip(lons.flatten(), lats.flatten()))
    points = MultiPoint(grid)

    mask = np.ones(shape=(spar_lon * spar_lat), dtype='bool')
    for ind, p in enumerate(points):
        if lake.intersects(p):
            mask[ind] = False
    mask = mask.reshape(spar_lat, spar_lon)

    ma_lons = ma.array(lons, mask=mask)
    ma_lats = ma.array(lats, mask=mask)

    with open('_lons.pkl', 'wb') as f:
        pickle.dump(ma_lons, f)
    with open('_lats.pkl', 'wb') as f:
        pickle.dump(ma_lats, f)


def read_raw(fname, variable_group='geophysical_data', variable='chlor_a'):
    """"""
    fh = nc.Dataset(fname, mode='r')

    nav = fh.groups['navigation_data']
    lons = nav.variables['longitude'][:]
    lats = nav.variables['latitude'][:]

    geo = fh.groups[variable_group]
    ch_a = geo.variables[variable][:]

    ma_lons = ma.array(lons, mask=ch_a.mask, fill_value=ch_a.fill_value)
    ma_lats = ma.array(lats, mask=ch_a.mask, fill_value=ch_a.fill_value)

    return ma_lons, ma_lats, ch_a


def interpolate(raw_lons, raw_lats, raw_ch_a, _lons, _lats):
    """"""
    # data from satellite
    raw_X = np.vstack((raw_lons.compressed(), raw_lats.compressed())).T
    raw_y = raw_ch_a.compressed()

    # interpolation grid
    int_X = np.vstack((_lons.flatten(), _lats.flatten())).T
    int_X_mask = np.ones(shape=(int_X.shape[0]), dtype='bool')

    # defining in which radius to interpolate
    min_grid_distance_lon = euclidean(ma.getdata(_lons)[0][0], ma.getdata(_lons)[0][1])
    min_grid_distance_lat = euclidean(ma.getdata(_lats)[0][0], ma.getdata(_lats)[1][0])
    min_grid_distance = custom_round(np.min([min_grid_distance_lat, min_grid_distance_lon]))

    # we define interpolation grid mask
    # leaving only those points that lie in min grid distance radius from true data
    tree = neighbors.KDTree(raw_X, leaf_size=2)
    for ind, x in enumerate(int_X):
        if tree.query_radius(x.reshape(1,-1), r=min_grid_distance, count_only=True)[0] > 0:
            int_X_mask[ind] = False
    int_X_mask = int_X_mask.reshape(_lons.shape)

    # interpolation
    knn = neighbors.KNeighborsRegressor(n_neighbors=3, weights='distance')
    T = np.vstack((_lons.flatten(), _lats.flatten())).T
    int_ch = knn.fit(raw_X, raw_y).predict(T)
    int_ch = int_ch.reshape(_lons.shape)
    masked_int_ch = ma.array(int_ch, mask=np.logical_or(_lons.mask, int_X_mask))
    return masked_int_ch
