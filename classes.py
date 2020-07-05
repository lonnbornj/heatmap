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
        pass


class Heatmap:

    time_evolution_dir = path.join("data", "time_evolved_data")

    def __init__(self, *activities):

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
        self.concatenated_activities = pd.concat(self.activity_dataframes)
        self.grid = Grid(self.activity_dataframes)
        self.add_grid_to_activities()
        self.time_evolve_cumulative_heat()


    def add_grid_to_activities(self):
        for i, df in enumerate(self.activity_dataframes):
            df["lat_inds"], df["lon_inds"] = self.grid.latlon_to_grid_indices(
                df["latitude"], df["longitude"]
            )
            self.activity_dataframes[i] = df

    def time_evolve_cumulative_heat(self):
        filenames = [
            os.path.join(
                self.time_evolution_dir, "".join([self.name, "_", str(i), ".pickle"])
            )
            for i in span["time"]["max"]
        ]
        for t, fname in enumerate(filenames):
            _next_cumulative_heat(t, fname)
        return cumulative_visits

    def _next_cumulative_heat(self, filename):
        for time_index in range(self.grid.span["time"]["max"]):
            if not path.isfile(filename):
                self.cumulative_visits = self._update_cell_heat(time_index)
            else:
                self.cumulative_visits = read_pickle(filename)
            yield

    def _update_cell_heat(time_index):
        delta_heat_of_cells = self._delta_heat(time_index)
        cumulative_at_t = pd.concat(
            [self.cumulative_visits, cell_visits_t], axis=1
        ).sum(axis=1)
        cumulative_at_t.to_pickle(filename)
        return cumulative_at_t

    def _delta_heat(self, time_index):
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

        self.dataframe_filenames = glob(path.join(self.pickle_path, name + "*.pickle"))
        assert (
            self.dataframe_filenames
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
        raw_data_paths, df_paths = _construct_file_paths_by_extension(ext)
        for raw_data_path, dataframe_path in zip(raw_data_paths, df_paths):
            if not path.isfile(df_path):
                convert.convert_raw(raw_data_path, dataframe_path)

    def _construct_file_paths_by_extension(ext):
        raw_data_paths = glob(path.join(self.raw_data_path, "*." + ext))
        df_basenames = [
            "_".join([self.name, ext, str(i)]) for i in range(len(raw_data_paths))
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
            "time": span_no_margin["time"],
        }
        return span

    def _latlon_delta(span):
        return (
            np.abs(span["lat"]["max"] - span["lon"]["min"]),
            np.abs(span["lon"]["max"] - span["lon"]["min"]),
        )


# j = Activities("Jack")
# t = Activities("Tenzin")
# hm = Heatmap(j, t)
# hm.animate()              # animates concurrently
# hm.plot_final_frame()

# //
# j = Activities("Jack")
# t = Activities("Tenzin")
# hm = Heatmap(j, t)
# hm.append_frames(j)
# hm.plot_final_frame()
# hm.append_frames(t)
# hm.animate()              # animates j followed by t
