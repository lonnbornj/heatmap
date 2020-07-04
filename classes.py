import pandas as pd
import numpy as np
from glob import glob
import os
import math
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

    def update_grid(self):

        self.grid = Grid(self.filenames)
        self._add_grid_indices()

    def _add_grid_indices(self):
        for fname in self.filenames:
            df = pd.read_pickle(fname)
            df["lat_inds"], df["lon_inds"] = self.grid.latlon_to_grid_indices(
                df["latitude"], df["longitude"]
            )
            df.to_pickle(fname)

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

    pickle_path = path.join("data", "pickles")

    def __init__(self, name):

        self.name = name
        self.raw_data_path = path.join("data", self.name, "raw")
        self.excluded_raw_data = path.join(self.raw_data_path, "exclude")
        self.raw_file_types = ["gpx", "tcx"]

        self._setup_directory_structure()
        self._create_dataframes()

        self.filenames = glob(path.join(self.pickle_path, name + "*.pickle"))
        assert (
            self.filenames
        ), "No GPS data found found. Place .gpx/.tcx files in {}".format(
            path.join("data", name)
        )

    def _setup_directory_structure(self):
        for d in [self.raw_data_path, self.pickle_path, self.excluded_raw_data]:
            if not path.exists(d):
                makedirs(d)

    def _create_dataframes():
        for extension in self.raw_file_types:
            for f in glob(path.join("data", name, "*." + extension)):
                rename(f, path.join(self.raw_data_path, path.basename(f)))
            self._pickle_raw_gps_data(extension)

    def _pickle_raw_gps_data(self, ext, low_speed_threshold=1):
        """
        Process and convert raw GPS data with extension ".gpx" or 
        ".tcx" to a pandas dataframe, and save as a .pickle file.
        """

        files = glob(path.join(self.raw_data_path, "*." + ext))
        for i, raw_data_path in enumerate(files):
            dataframe_basename = self.name + path.basename(
                raw_data_path.replace(ext, "pickle")
            )
            dataframe_path = path.join(self.pickle_path, dataframe_basename)
            if not path.isfile(df_path):
                convert.convert_raw(raw_data_path, dataframe_path)


class Grid:
    def __init__(self, activity_filenames, cell_size_m=10):

        self.activity_filenames = activity_filenames
        self.cell_size_m = cell_size_m
        self.set_spacetime_properties()
        self.empty = np.zeros([*self.num_cells.values()], dtype=np.uint16)

    def set_spacetime_properties(self, margin_size=0.05):

        df_all = pd.concat(pd.read_pickle(fname) for fname in self.activity_filenames)
        span_no_margin = _span_no_margin(df_all)

        self.cell_size_deg = geo.cell_size_deg(
            self.cell_size_m, latitude=np.mean([*span_no_margin["lat"].values()])
        )
        self.num_cells = _num_cells(span_no_margin, margin_size, self.cell_size_deg)
        self.span = _span_with_margin(span_no_margin, margin_size)

    def latlon_to_grid_indices(self, lats, lons):

        dlats = lats - self.span["lat"]["min"]
        dlons = lons - self.span["lon"]["min"]
        assert (
            all(dlats) > 0 and all(dlons) > 0
        ), "latlon passed which is outside grid domain"

        lat_inds = np.floor(dlats / self.cell_size_deg["lat"]).astype(int)
        lon_inds = np.floor(dlons / self.cell_size_deg["lon"]).astype(int)
        return lat_inds, lon_inds

    def _num_cells(span_no_margin, margin_size, cell_size_deg):
        return {
            "lat": np.ceil(
                (1 + 2 * margin_size) * dlat / self.cell_size_deg["lat"]
            ).astype(int),
            "lon": np.ceil((1 + 2 * margin_size) * dlon / cell_size_deg["lon"]).astype(
                int
            ),
        }

    def _span_no_margin(df_all):
        span = dict()
        span["lat"] = {"min": df_all["latitude"].min(), "max": df_all["latitude"].max()}
        span["lon"] = {
            "min": df_all["longitude"].min(),
            "max": df_all["longitude"].max(),
        }
        span["time"] = {"min": 0, "max": df_all.index.max()}
        return span

    def _span_with_margin(span_no_margin, margin_size):
        def get_1d_span(minimum, cell_size, num_cells):
            return {"min": minimum, "max": minimum + cell_size * num_cells}

        dlat, dlon = self._latlon_delta(span_no_margin)
        span = {
            "lat": get_1d_span(
                span_no_margin["lat"]["min"] - margin_size * dlat,
                self.cell_size_deg["lat"],
                self.num_cells["lat"],
            ),
            "lon": get_1d_span(
                span_no_margin["lon"]["min"] - margin_size * dlon,
                self.cell_size_deg["lon"],
                self.num_cells["lon"],
            ),
            "time": span_no_margin["time"]
        }
        return span

    def _latlon_delta(span):
        return (
            np.abs(span["lat"]["max"] - span["lon"]["min"]),
            np.abs(span["lon"]["max"] - span["lon"]["min"]),
        )


# j = Activities("Jack")
# t = Activities("Tenzin")
# hm = Heatmap("Jack", "Tenzin")
# a = Activities("Anika")
# hm.add(a)
# hm.update_grid()
# hm.animate()
# hm.plot_final_frame()
