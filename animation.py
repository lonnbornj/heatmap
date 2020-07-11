import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d.axes3d import Axes3D
import numpy as np



class Animation:
    def __init__(self, blank_grid, data):
        self.blank_grid = np.zeros([i*2 for i in blank_grid.shape])
        self.data = data
        self.num_frames = len(self.data)

    def animate(self):
        fig = plt.figure()
        ax = plt.axes()
        anim = animation.FuncAnimation(
            fig, self.create_frame, frames = np.arange(self.num_frames), fargs=(ax,), interval=1
        )
        plt.show()

    def create_frame(self, t, ax):
        frame = self.blank_grid.copy()
        lat_inds, lon_inds, heat = self.get_latlon_heat(t)
        frame[lat_inds, lon_inds] += heat
        ax.clear()
        ax.imshow(frame)
        # ax.set_xlim([200, 500])
        # ax.set_ylim([1200, 1650])
        return ax

    def plot_final_frame(self):
        fig = plt.figure()
        ax = plt.axes()
        ax = self.create_frame(self.num_frames-1, ax)
        plt.show()


    def get_latlon_heat(self, t):
        lat_inds, lon_inds = np.array([pair for pair in zip(*self.data[t].index)])
        normed_heat = self.normalise(self.data[t].values)
        return [lat_inds, lon_inds, normed_heat]


    def normalise(self, heat):
        cdf_of_heat = np.cumsum(np.bincount(heat))/heat.size
        return cdf_of_heat[heat]

