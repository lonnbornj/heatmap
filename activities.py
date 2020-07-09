from glob import glob
import os

import convert


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

        self.dataframe_filenames = glob(
            os.path.join(self.pickle_path, name + "*.pickle")
        )
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
            "_".join([self.name, ext, str(i)]) + ".pickle"
            for i in range(len(raw_data_paths))
        ]
        df_paths = [os.path.join(self.pickle_path, base) for base in df_basenames]
        return raw_data_paths, df_paths
