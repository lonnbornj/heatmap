import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import imageio
import os
import glob

from setup_manager import SetupManager


class Animation:

    setup_manager = SetupManager()
    frames_dir = setup_manager.frames_dir

    def __init__(self, name, blank_grid, data):
        self.name = name
        self.blank_grid = blank_grid
        self.data = data
        self.num_frames = len(self.data)

    def animate(self, save = False):
        print("creating animation...")
        fig = plt.figure()
        ax = plt.axes()
        for t in range(self.num_frames):
            ax = self.create_frame(t, ax)
            # fig_fname = self.name + str(t).zfill(len(str(self.num_frames))) + ".png"
            # fig.savefig(os.path.join(self.frames_dir, fig_fname))
            # plt.show()
        images = []
        for filename in sorted(glob.glob(os.path.join(self.frames_dir, '*.png'))):
            images.append(imageio.imread(filename))
        imageio.mimsave('test.gif', images)

    def create_frame(self, t, ax):
        fig = plt.figure()
        ax = plt.axes()
        frame = self.blank_grid.copy()
        lat_inds, lon_inds, heat = self.get_latlon_heat(t)
        frame[lat_inds, lon_inds] += heat

        cmap = plt.cm.viridis
        frame = np.ma.masked_where(frame == 0, frame)  # hack to make background black
        cmap.set_bad(color="black")
        ax.clear()
        ax.imshow(frame, interpolation="none", cmap=cmap)
        ax.set_xlim([400, 1000])
        ax.set_ylim([1200, 1800])
        # plt.show()
        fig_fname = self.name + str(t).zfill(len(str(self.num_frames))) + ".png"
        fig.savefig(os.path.join(self.frames_dir, fig_fname))
        plt.close()
        return ax

    def plot_final_frame(self):
        fig = plt.figure()
        ax = plt.axes()
        ax = self.create_frame(self.num_frames - 1, ax)
        plt.show()
        plt.savefig

    def get_latlon_heat(self, t):
        lat_inds, lon_inds = np.array([pair for pair in zip(*self.data[t].index)])
        normed_heat = self.normalise(self.data[t].values)
        # normed_heat = self.data[t].values
        return [lat_inds, lon_inds, normed_heat]

    def normalise(self, heat):
        cdf_of_heat = np.cumsum(np.bincount(heat)) / heat.size
        return cdf_of_heat[heat]
