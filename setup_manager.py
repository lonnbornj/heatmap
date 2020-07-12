import os
import glob


class SetupManager:
    def __init__(self, data_root="/main_1TB/hm_data"):

        self.data_root_dir = data_root
        self.activities_pickles_dir = os.path.join(self.data_root_dir, "pickles")
        self.heatmap_data_dir = os.path.join(self.data_root_dir, "heatmap")
        self.frames_dir = os.path.join(self.data_root_dir, "frames")

    def setup_directory_structure(self, name):

        raw_data_dir = self.get_raw_data_dir(name)
        excluded_raw_data = os.path.join(raw_data_dir, "excluded")
        directories = [
            self.activities_pickles_dir,
            self.heatmap_data_dir,
            self.frames_dir,
            raw_data_dir,
            excluded_raw_data,
        ]
        for d in directories:
            if not os.path.exists(d):
                os.makedirs(d)

    def reset(self, name, which="all"):

        output_directories = {
            "activities": self.activities_pickles_dir,
            "heatmap": self.heatmap_data_dir,
            "frames": self.frames_dir,
        }
        self.remove_output_files(output_directories, which)
        self.replace_excluded_files(name)

    def remove_output_files(self, output_directories, which):
        if which == "all":
            dirs_to_remove = [d for d in output_directories.values()]
        else:
            dirs_to_remove = [output_directories[which]]
        for d in dirs_to_remove:
            for f in glob.glob(os.path.join(d, "*.pickle")):
                os.remove(f)

    def replace_excluded_files(self, name):
        raw_data_dir = self.get_raw_data_dir(name)
        excluded_data_dir = self.get_excluded_data_dir(name)
        for f in glob.glob(os.path.join(excluded_data_dir, "*")):
            os.rename(
                f, os.path.join(raw_data_dir, os.path.basename(f)),
            )

    def get_raw_data_dir(self, name):
        return os.path.join(self.data_root_dir, name)

    def get_excluded_data_dir(self, name):
        return os.path.join(self.data_root_dir, name, "excluded")

    def construct_heatmap_filenames(self, name, max_time):
        return [
            os.path.join(self.heatmap_data_dir, "".join([name, "_", str(i), ".pickle"]))
            for i in range(max_time)
        ]

    def construct_activity_filenames(self, name, ext):
        raw_data_path = self.get_raw_data_dir(name)
        raw_data_fnames = glob.glob(os.path.join(raw_data_path, "*." + ext))
        df_basenames = [
            "_".join([name, ext, str(i)]) + ".pickle"
            for i in range(len(raw_data_fnames))
        ]
        df_paths = [
            os.path.join(self.activities_pickles_dir, base) for base in df_basenames
        ]
        return raw_data_fnames, df_paths
