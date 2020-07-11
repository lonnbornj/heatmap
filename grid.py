import pandas as pd
import numpy as np
import geometry


class Grid:
    def __init__(self, activity_dataframes, cell_size_m=10):

        self.activity_dataframes = activity_dataframes
        self.cell_size_m = cell_size_m
        self.set_grid_properties()
        self.empty = np.zeros([*self.num_cells.values()], dtype=np.uint16)

    def set_grid_properties(self, margin_size=0.05):

        df_all = pd.concat(self.activity_dataframes)
        span_no_margin = self.compute_span_no_margin(df_all)
        self.cell_size_deg = geometry.cell_size_deg(
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
        dlat, dlon = self.compute_latlon_delta(span_no_margin)
        return {
            "lat": np.ceil(
                (1 + 2 * margin_size) * dlat / self.cell_size_deg["lat"]
            ).astype(int),
            "lon": np.ceil(
                (1 + 2 * margin_size) * dlon / self.cell_size_deg["lon"]
            ).astype(int),
        }

    def compute_span_no_margin(self, df_all):
        span = dict()
        span["lat"] = {"min": df_all["latitude"].min(), "max": df_all["latitude"].max()}
        span["lon"] = {
            "min": df_all["longitude"].min(),
            "max": df_all["longitude"].max(),
        }
        span["time"] = {"min": 0, "max": df_all.index.max() - 1}
        return span

    def compute_span_with_margin(self, span_no_margin, margin_size):
        def get_1d_span(minimum, cell_size, num_cells):
            return {"min": minimum, "max": minimum + cell_size * num_cells}

        dlat, dlon = self.compute_latlon_delta(span_no_margin)
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

    def compute_latlon_delta(self, span):
        return (
            np.abs(span["lat"]["max"] - span["lat"]["min"]),
            np.abs(span["lon"]["max"] - span["lon"]["min"]),
        )
