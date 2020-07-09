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
    def __init__(self, grid, ):
        self.heatmap = heatmap
        self.grid = self.heatmap.grid.empty

    def plot_frame(self, t):
        # heatmap.next_cumulative_heat
        pass


class Heatmap:

    heatmap_data_dir = os.path.join("data", "heatmap")
    if not os.path.exists(heatmap_data_dir):
    	os.makedirs(heatmap_data_dir)

    def __init__(self, *activities_objects):

        self.activities_objects = activities_objects
        self.name = "".join(a.name for a in activities_objects)
        self.dataframe_filenames = [
            fname
            for activity_obj in activities_objects
            for fname in activity_obj.dataframe_filenames
        ]
        self.activity_dataframes = [
            pd.read_pickle(fname) for fname in self.dataframe_filenames
        ]
        self.grid = Grid(self.activity_dataframes)
        self.activity_dataframes = self.add_grid_indices_to_activities()
        self.concatenated_activities = pd.concat(self.activity_dataframes)
        self.data = dict()
        self.time_evolve_map()


    def add_grid_indices_to_activities(self):
        for i, df in enumerate(self.activity_dataframes):
            df["lat_inds"], df["lon_inds"] = self.grid.latlon_to_grid_indices(
                df["latitude"], df["longitude"]
            )
            self.activity_dataframes[i] = df
        return self.activity_dataframes

    def time_evolve_map(self):
        filenames = [
            os.path.join(
                self.heatmap_data_dir, "".join([self.name, "_", str(i), ".pickle"])
            )
            for i in range(self.grid.span["time"]["max"] + 1)
        ]
        self.cumulative_cell_heat = pd.DataFrame()
        for t, fname in enumerate(filenames):
            self.next_cumulative_heat(t, fname)
            print(t)
            print(self.cumulative_cell_heat)
            self.data[t] = self.cumulative_cell_heat

    def next_cumulative_heat(self, time_index, filename):
        if not os.path.isfile(filename):
            self.cumulative_cell_heat = self.update_cell_heat(time_index)
            self.cumulative_cell_heat.to_pickle(filename)
        else:
            self.cumulative_cell_heat = pd.read_pickle(filename)

    def update_cell_heat(self, time_index):
        delta_heat_of_cells = self.delta_heat(time_index)
        cumulative_at_t = pd.concat(
            [self.cumulative_cell_heat, delta_heat_of_cells], axis=1
        ).sum(axis=1)
        return cumulative_at_t

    def delta_heat(self, time_index):
        return (
            self.concatenated_activities[
                self.concatenated_activities.index == time_index
            ][["lat_inds", "lon_inds"]]
            .groupby(["lat_inds", "lon_inds"])
            .size()
        )

    def animate():
        pass


class Activities:
    """
    A collection of processed GPS data.
    """

    pickle_path = os.path.join("data", "pickles")

    def __init__(self, name):

        self.name = name
        self.raw_data_path = os.path.join("data", self.name)
        self.excluded_raw_data = os.path.join(self.raw_data_path, "exclude")
        self.raw_file_types = ["gpx", "tcx"]

        self.setup_directory_structure()
        self.create_dataframes()

        self.dataframe_filenames = glob(os.path.join(self.pickle_path, name + "*.pickle"))
        assert (
            self.dataframe_filenames
        ), "No GPS data found found. Place .gpx/.tcx files in {}".format(
            os.path.join("data", name)
        )

    def setup_directory_structure(self):
        for d in [self.raw_data_path, self.pickle_path, self.excluded_raw_data]:
            if not os.path.exists(d):
                os.makedirs(d)

    def create_dataframes(self):
        for extension in self.raw_file_types:
            for f in glob(os.path.join("data", self.name, "*." + extension)):
                os.rename(f, os.path.join(self.raw_data_path, os.path.basename(f)))
            self.pickle_raw_gps_data(extension)

    def pickle_raw_gps_data(self, ext, low_speed_threshold=1):
        """
        Process and convert raw GPS data with extension ".gpx" or 
        ".tcx" to a pandas dataframe, and save as a .pickle file.
        """
        raw_data_paths, df_paths = self.construct_file_paths_by_extension(ext)
        for raw_data_path, dataframe_path in zip(raw_data_paths, df_paths):
            if not os.path.isfile(dataframe_path):
                convert.convert_raw(raw_data_path, dataframe_path)

    def construct_file_paths_by_extension(self, ext):
        raw_data_paths = glob(os.path.join(self.raw_data_path, "*." + ext))
        df_basenames = [
            "_".join([self.name, ext, str(i)]) + ".pickle" for i in range(len(raw_data_paths))
        ]
        df_paths = [os.path.join(self.pickle_path, base) for base in df_basenames]
        return raw_data_paths, df_paths


class Grid:
    def __init__(self, activities, cell_size_m=10):

        self.activities = activities
        self.cell_size_m = cell_size_m
        self.set_grid_properties()
        self.empty = np.zeros([*self.num_cells.values()], dtype=np.uint16)

    def set_grid_properties(self, margin_size=0.05):

        df_all = pd.concat(self.activities)
        span_no_margin = self.compute_span_no_margin(df_all)
        self.cell_size_deg = geo.cell_size_deg(
            self.cell_size_m, latitude=np.mean([*span_no_margin["lat"].values()])
        )
        self.num_cells = self.compute_num_cells(span_no_margin, margin_size)
        self.span = self.compute_span_with_margin(span_no_margin, margin_size)

    def latlon_to_grid_indices(self, lats, lons):

        dlats = lats - self.span["lat"]["min"]
        dlons = lons - self.span["lon"]["min"]
        assert (
            all(dlats) > 0 and all(dlons) > 0
        ), "latlon passed which is outside grid domain"

        lat_inds = np.floor(dlats / self.cell_size_deg["lat"]).astype(int)
        lon_inds = np.floor(dlons / self.cell_size_deg["lon"]).astype(int)
        return lat_inds, lon_inds

    def compute_num_cells(self, span_no_margin, margin_size):
        dlat, dlon = self.latlon_delta(span_no_margin)
        return {
            "lat": np.ceil(
                (1 + 2 * margin_size) * dlat / self.cell_size_deg["lat"]
            ).astype(int),
            "lon": np.ceil((1 + 2 * margin_size) * dlon / self.cell_size_deg["lon"]).astype(
                int
            ),
        }

    def compute_span_no_margin(self, df_all):
        span = dict()
        span["lat"] = {"min": df_all["latitude"].min(), "max": df_all["latitude"].max()}
        span["lon"] = {
            "min": df_all["longitude"].min(),
            "max": df_all["longitude"].max(),
        }
        span["time"] = {"min": 0, "max": df_all.index.max()}
        return span

    def compute_span_with_margin(self, span_no_margin, margin_size):
        def get_1d_span(minimum, cell_size, num_cells):
            return {"min": minimum, "max": minimum + cell_size * num_cells}

        dlat, dlon = self.latlon_delta(span_no_margin)
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
            "time": span_no_margin["time"],
        }
        return span

    def latlon_delta(self, span):
        return (
            np.abs(span["lat"]["max"] - span["lon"]["min"]),
            np.abs(span["lon"]["max"] - span["lon"]["min"]),
        )


t = Activities("test")
# t = Activities("Tenzin")
hm = Heatmap(t)
# hm.animate()              # animates concurrently
# hm.plot_final_frame()
