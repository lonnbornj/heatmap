from glob import glob
import os

from setup_manager import SetupManager
import convert


class Activities:
    """
    A collection of processed GPS data.
    """

    setup_manager = SetupManager()
    pickle_path = setup_manager.activities_pickles_dir

    def __init__(self, name):

        self.name = name
        self.setup_manager.setup_directory_structure(self.name)
        self.raw_data_path = self.setup_manager.get_raw_data_dir(self.name)
        self.excluded_raw_data = self.setup_manager.get_excluded_data_dir(self.name)

        self.raw_file_types = ["gpx", "tcx"]
        self.create_dataframes()

        self.dataframe_filenames = glob(
            os.path.join(self.pickle_path, name + "*.pickle")
        )
        assert (
            self.dataframe_filenames
        ), "No GPS data found found. Place .gpx/.tcx files in {}".format(
            os.path.join("data", name)
        )

    def create_dataframes(self):
        for extension in self.raw_file_types:
            for f in glob(os.path.join("data", self.name, "*." + extension)):
                os.rename(f, os.path.join(self.raw_data_path, os.path.basename(f)))
            self.pickle_raw_gps_data(extension)

    def pickle_raw_gps_data(self, ext, low_speed_threshold=1):
        """
        Process and convert raw GPS data with extension ".gpx" or 
        ".tcx" to a pandas dataframe and pickle.
        """
        raw_data_paths, df_paths = self.setup_manager.construct_activity_filenames(
            self.name, ext
        )
        for raw_data_path, dataframe_path in zip(raw_data_paths, df_paths):
            if not os.path.isfile(dataframe_path):
                convert.convert_raw(
                    raw_data_path, self.excluded_raw_data, dataframe_path
                )
