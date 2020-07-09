import pandas as pd
import os
from grid import Grid


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
            .astype(np.uint16)
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

    def animate():
        pass
