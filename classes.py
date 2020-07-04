import pandas as pd
import numpy as np
from glob import glob
import os
import math
import gpxpy
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import geometry as geo
import convert


class Animation:
    def __init__(self, heatmap):
        self.heatmap = heatmap
        self.grid = self.heatmap.grid.empty

    def plot_frame(self, t):

        # https://pythonspeed.com/articles/numpy-memory-footprint/
        data = pd.read_pickle(self.heatmap.filenames[t])
        inds = [list(i) for i in zip(*data.index)]

        data = sparse.COO(data)
        return data


class Heatmap:
    def __init__(self, data_dir):

        self.activities = Activities(data_dir)
        self.time_evol_dir = path.join("data", data_dir, "time_evol")
        if not path.exists(self.time_evol_dir):
            makedirs(self.time_evol_dir)
        self.grid = self.activities.grid
        self.fname_len = len(str(self.grid.span["time"]))
        self.df_all = pd.concat(
            pd.read_pickle(fname) for fname in self.activities.filenames
        )
        self.cumulative_visits = (
            self.df_all[self.df_all.index == 0][["lat_inds", "lon_inds"]]
            .groupby(["lat_inds", "lon_inds"])
            .size()
        )
        for t in range(1, self.grid.span["time"]):
            filename = path.join(
                self.time_evol_dir, str(t).zfill(self.fname_len) + ".pickle"
            )
            if not path.isfile(filename):
                if t % 10 == 0:
                    print(t)
                self.step_cumulative_visits(t, filename)
        self.filenames = glob(path.join(self.time_evol_dir, "*.pickle"))

    def step_cumulative_visits(self, t, filename):
        df_t = self.df_all[self.df_all.index == t][["lat_inds", "lon_inds"]]
        cell_visits_t = df_t.groupby(["lat_inds", "lon_inds"]).size()
        self.cumulative_visits = pd.concat(
            [self.cumulative_visits, cell_visits_t], axis=1
        ).sum(axis=1)
        self.cumulative_visits.to_pickle(filename)

    def animate():
        pass


class Activities:
    """
    A collection of dataframes (saved as pickles), each of 
    which is associated with an activity. Each dataframe is a 
    processed a .gpx or .tcx file containing raw GPS data.
    """

    def __init__(self, name):

        self.raw_data_path = path.join("data", name, "raw")
        self.excluded_raw_data = path.join(self.raw_data_path, "exclude")
        self.pickle_paths = path.join("data", name, "pickles")
        self.raw_file_types = ["gpx", "tcx"]

        for d in [self.raw_data_path, self.pickle_path, self.excluded_raw_data]:
            if not path.exists(d):
                makedirs(d)

        for extension in self.raw_file_types:
            for f in glob(path.join("data", name, "*." + extension)):
                rename(f, path.join(self.raw_data_path, path.basename(f)))
            self.pickle_raw_gps_data(extension)

        self.filenames = glob(path.join(self.pickle_path, "*.pickle"))

        assert (
            self.filenames
        ), "No GPS data found found. Place .gpx/.tcx files in {}".format(
            path.join("data", name)
        )

    # def __add__(self, other):

    # 	name = self.raw_data_path.split(os.sep)[-2] + other.raw_data_path.split(os.sep)[-2]
    # 	pickle_paths

    def update_grid(self):

        self.grid = Grid(self.filenames)
        self._add_grid_indices()

    def pickle_raw_gps_data(self, ext, low_speed_threshold=1):
        """
        Process and convert raw GPS data with extension ".gpx" or 
        ".tcx" to a pandas dataframe, and save as a .pickle file.
        """

        files = glob(path.join(self.raw_data_path, "*." + ext))
        for i, fname in enumerate(files):
            df_basename = path.basename(fname.replace(ext, "pickle"))
            df_path = path.join(self.pickle_path, df_basename)

            if not path.isfile(df_path):

                print("processing {}".format(path.basename(fname)))
                df = (
                    convert.gpx_to_dataframe(fname)
                    if ext == "gpx"
                    else convert.tcx_to_dataframe(fname)
                )
                if df is None:
                    rename(
                        fname, path.join(self.excluded_raw_data, path.basename(fname))
                    )
                else:
                    df.to_pickle(df_path)

    def _add_grid_indices(self):
        for fname in self.filenames:
            df = pd.read_pickle(fname)
            df["lat_inds"], df["lon_inds"] = self.grid.latlon_to_indices(
                df["latitude"], df["longitude"]
            )
            df.to_pickle(fname)


class Grid:
    def __init__(self, activity_filenames, cell_size_m=10):

        self.activity_filenames = activity_filenames
        self.cell_size_m = cell_size_m
        self.span, self.num_cells, self.cell_size_deg = self.spacetime_span()
        self.empty = np.zeros([*self.num_cells.values()], dtype=np.uint16)

    def spacetime_span(self):

        df_all = pd.concat(pd.read_pickle(fname) for fname in self.activity_filenames)

        lat_min_temp, lat_max_temp, lon_min_temp, lon_max_temp = (
            df_all["latitude"].min(),
            df_all["latitude"].max(),
            df_all["longitude"].min(),
            df_all["longitude"].max(),
        )
        cell_size_deg = {
            "lat": geo.dist_to_dlat(self.cell_size_m),
            "lon": geo.dist_to_dlon(
                self.cell_size_m, np.mean([lat_min_temp, lat_max_temp])
            ),
        }
        dlat, dlon = (
            np.abs(lat_max_temp - lat_min_temp),
            np.abs(lon_max_temp - lon_min_temp),
        )
        num_cells = {
            "lat": np.ceil(1.1 * dlat / cell_size_deg["lat"]).astype(int),
            "lon": np.ceil(1.1 * dlon / cell_size_deg["lon"]).astype(int),
        }
        span = {
            "lat": (
                lat_min_temp - 0.05 * dlat,
                num_cells["lat"] * cell_size_deg["lat"] + lat_min_temp - 0.05 * dlat,
            ),
            "lon": (
                lon_min_temp - 0.05 * dlon,
                num_cells["lon"] * cell_size_deg["lon"] + lon_min_temp - 0.05 * dlon,
            ),
            "time": df_all.index.max(),
        }

        return span, num_cells, cell_size_deg

    def latlon_to_indices(self, lats, lons):

        dlats = np.abs(self.span["lat"][0] - lats)
        dlons = np.abs(self.span["lon"][0] - lons)
        lat_inds = np.floor(dlats / self.cell_size_deg["lat"]).astype(int)
        lon_inds = np.floor(dlons / self.cell_size_deg["lon"]).astype(int)
        return lat_inds, lon_inds


hm = Heatmap("jack")
ani = Animation(hm)
data = ani.plot_frame(30)
