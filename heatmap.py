import pandas as pd
import numpy as np
import os
from grid import Grid
from setup_manager import SetupManager


class Heatmap:

    setup_manager = SetupManager()
    pickle_path = setup_manager.heatmap_data_dir

    def __init__(self, *activities_objects):

        self.activities_objects = activities_objects
        self.name = "".join(a.name for a in activities_objects)
        dataframe_filenames = [
            fname
            for activity_obj in activities_objects
            for fname in activity_obj.dataframe_filenames
        ]
        self.activity_dataframes = [
            pd.read_pickle(fname) for fname in dataframe_filenames
        ]
        # todo: add method to remove outlier activities,
        # characterised by <mean(lat), mean(lon)>

        self.grid = Grid(self.activity_dataframes)
        self.activity_dataframes = self.add_grid_indices_to_activities()
        self.concatenated_activities = pd.concat(self.activity_dataframes)
        self.data = dict()
        self.time_evolve_map()

    def remove_outlier_activities(self):
        average_latlon = np.nan * np.ones(len(self.activity_dataframes), 2)
        for i, df in enumerate(self.activity_dataframes):
            average_latlon[i, :] = df.mean()

    def add_grid_indices_to_activities(self):
        # todo: add hit to grids that get skipped because the subject
        # is moving faster than the time resolution of the gps data.
        for i, df in enumerate(self.activity_dataframes):
            df["lat_inds"], df["lon_inds"] = self.grid.latlon_to_grid_indices(
                df["latitude"], df["longitude"]
            )
            df = self.fill_gaps_in_path(df)
            self.activity_dataframes[i] = df
        return self.activity_dataframes


    def time_evolve_map(self):
        print("evolving heatmap in time...")
        filenames = self.setup_manager.construct_heatmap_filenames(
            self.name, self.grid.span["time"]["max"]
        )
        self.cumulative_cell_heat = pd.DataFrame()
        for t, fname in enumerate(filenames):
            self.next_cumulative_heat(t, fname)
            self.data[t] = self.cumulative_cell_heat.copy()

    def next_cumulative_heat(self, time_index, filename):
        if not os.path.isfile(filename):
            self.cumulative_cell_heat = self.update_cell_heat(time_index)
            self.cumulative_cell_heat.to_pickle(filename)
        else:
            self.cumulative_cell_heat = pd.read_pickle(filename)

    def update_cell_heat(self, time_index):
        delta_heat_of_cells = self.delta_heat(time_index)
        cumulative_at_t = (
            pd.concat([self.cumulative_cell_heat, delta_heat_of_cells], axis=1)
            .sum(axis=1)
            .astype(np.uint32)
        )
        return cumulative_at_t

    def delta_heat(self, time_index):
        return (
            self.concatenated_activities[
                self.concatenated_activities.index == time_index
            ][["lat_inds", "lon_inds"]]
            .groupby(["lat_inds", "lon_inds"])
            .size()
        )

    def fill_gaps_in_path(self, df):

        jump_mask = abs(df.diff()) != 1
        if jump_mask.sum().sum() > 0:
            fill_vals = self.find_gaps_in_path(df, jump_mask)
            df = (
                pd.concat([df, fill_vals])
                .fillna(method="ffill")
                .drop_duplicates()
                .astype(np.uint32)
            )
        return df

    def find_gaps_in_path(self, df, jump_mask):
        max_cells_jumped = df.diff().max().max().astype(int)
        print(max_cells_jumped)
        fill_vals = pd.concat(
            [
                df.diff()[jump_mask] * i / max_cells_jumped
                for i in range(1, max_cells_jumped)
            ]
        )
        fill_vals = (df - fill_vals.round()).dropna(how="all")

        return fill_vals
