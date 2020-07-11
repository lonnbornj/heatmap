import os
import glob


class SetupManager:
    def __init__(self, data_root):

        self.data_root_dir = data_root
        self.activities_pickles_dir = os.path.join(self.data_root_dir, "pickles")
        self.heatmap_data_dir = os.path.join(self.data_root_dir, "heatmap")

    def setup_directory_structure(self, name):

        raw_data_dir = get_raw_data_dir(name)
        excluded_raw_data = os.path.join(raw_data_dir, "excluded")
        directories = [
            self.activities_pickles_dir,
            self.heatmap_data_dir,
            raw_data_dir,
            excluded_raw_data,
        ]
        for d in directories:
            if not os.path.exists(d):
                os.makedirs(d)

    def delete_output_files(self, which="all"):

        output_directories = {
            "activities": self.activities_pickles_dir,
            "heatmap": self.heatmap_data_dir,
        }
        if which == "all":
            dirs_to_remove = [self.activities_pickles_dir, self.heatmap_data_dir]
        else:
            dirs_to_remove = [output_directories[which]]
        for d in dirs_to_remove:
            for f in glob.glob(os.path.join(d, "*")):
                os.remove(f)

    def get_raw_data_dir(name):
        return os.path.join(self.data_root_dir, name)

    def get_excluded_data_dir(name):
        return os.path.join(self.data_root_dir, name, "excluded")

    def construct_heatmap_filenames(name, max_time):
        return [
            os.path.join(self.heatmap_data_dir, "".join([name, "_", str(i), ".pickle"]))
            for i in range(max_time)
        ]

    def construct_activity_filenames(self, name, ext):
        raw_data_path = self.get_raw_data_dir(name)
        raw_data_fnames = glob(os.path.join(self.raw_data_path, "*." + ext))
        df_basenames = [
            "_".join([name, ext, str(i)]) + ".pickle"
            for i in range(len(raw_data_fnames))
        ]
        df_paths = [
            os.path.join(self.activities_pickles_dir, base) for base in df_basenames
        ]
        return raw_data_paths, df_paths
