import pandas as pd
import numpy as np
import glob
import shutil
from os import path, makedirs, rename
import gpxpy
import tcxparser

from geometry import add_speed_column


def convert_raw(raw_data_path, excluded_raw_data):
    # todo use SetupManager here instead of passing args
    print("processing {}".format(path.basename(raw_data_path)))
    _, ext = path.splitext(raw_data_path)
    df = (
        gpx_to_dataframe(raw_data_path)
        if ext == ".gpx"
        else tcx_to_dataframe(raw_data_path)
    )
    return df


def gpx_to_dataframe(filename):

    with open(filename, "r") as f:
        gpx = gpxpy.parse(f)

    data = []
    for track in gpx.tracks:
        for segment in track.segments:
            for i, point in enumerate(segment.points):
                data.append([point.time, point.latitude, point.longitude])
    df = pd.DataFrame(data, columns=["time", "latitude", "longitude"])

    df = clean(df)
    return df


def tcx_to_dataframe(filename):

    with open(filename, "r") as f:
        lines = f.readlines()
    lines[0] = lines[0].lstrip()
    with open(filename, "w") as f:
        f.writelines(lines)

    tcx = tcxparser.TCXParser(filename)

    time = tcx.time_values()
    positions = tcx.position_values()
    latitude, longitude = zip(*positions)
    altitude = tcx.altitude_points()

    speed = np.nan * np.ones([len(time), 1])

    df = pd.DataFrame(
        zip(*[time, latitude, longitude]), columns=["time", "latitude", "longitude"],
    )

    df = clean(df)
    return df


def clean(df):
    """Remove pauses, and return only the required columns"""
    df = add_speed_column(df)
    df.index = df.index.round("S")
    df = df.reset_index()
    df["delta"] = (df["time"] - df["time"].shift()).fillna(
        value=pd.Timedelta(seconds=0)
    )
    df = df.drop(
        df[(df["speed"] < 1) | (df["delta"] > pd.Timedelta(seconds=1.1))].index
    ).dropna()
    if len(df) < 10:
        print("Less than 10 rows. Skipping.")
        return None
    assert df["delta"].median() == pd.Timedelta(
        seconds=1
    ), "Median time step in file {} not equal to 1 second."
    return df[["latitude", "longitude"]].reset_index()
