import math
import numpy as np
from scipy.optimize import fsolve
import pandas as pd

R_EARTH = 6373.1 * 1e3  # m


def geodesic_dist(coords0, coords1):
    """Haversine formula."""

    lat0, lon0 = [math.radians(c) for c in coords0]
    lat0, lon1 = [math.radians(c) for c in coords1]
    dlat = lat1 - lat0
    dlon = lon1 - lon0

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat0) * math.cos(lat1) * math.sin(dlon / 2) ** 2
    )

    return 2 * R_EARTH * math.atan2(math.sqrt(a), math.sqrt(1 - a))  # km


def dist_to_dlat(dist):
    """Inverse Haversine formula for the latitude."""
    return math.degrees(dist / R_EARTH)


def dist_to_dlon(dist, dlat_mean):
    """Inverse Haversine formula for the longitude, at a given latitude."""
    c = dist / R_EARTH
    Y = math.cos(math.radians(dlat_mean))
    f = lambda x: Y * math.sin(x) / math.sqrt(1 - (Y * math.sin(x)) ** 2)
    g = lambda x: f(x) - math.tan(c / 2)
    x0 = math.radians(1e-4)
    x = fsolve(g, x0)
    return math.degrees(2 * x)


def cell_size_deg(cell_size_m, latitude):
    return {
        "lat": dist_to_dlat(cell_size_m),
        "lon": dist_to_dlon(cell_size_m, latitude),
    }


def add_speed_column(df):

    # todo: work out what the reindexing is doing and move it out of this fn
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time")
    columns = df.columns.tolist()

    df["theta"] = np.deg2rad(df["longitude"])
    df["phi"] = np.deg2rad(df["latitude"])
    df["x"] = R_EARTH * np.cos(df["theta"]) * np.sin(df["phi"])
    df["y"] = R_EARTH * np.sin(df["theta"]) * np.sin(df["phi"])
    df["z"] = R_EARTH * np.cos(df["phi"])
    df["x2"] = df["x"].shift()
    df["y2"] = df["y"].shift()
    df["z2"] = df["z"].shift()
    df["central angle"] = np.arccos(
        (df["x"] * df["x2"] + df["y"] * df["y2"] + df["z"] * df["z2"]) / (R_EARTH) ** 2
    )
    df["arclength"] = df["central angle"] * R_EARTH

    df["time"] = df.index.to_series().diff() / pd.Timedelta(seconds=1)
    df["speed"] = df["arclength"] / df["time"]  # in meters/second

    return df[columns + ["speed"]]
