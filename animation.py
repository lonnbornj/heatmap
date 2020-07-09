import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from numpy import arange
import numpy as np


class Animation:
    def __init__(self, blank_grid, data):
        self.blank_grid = blank_grid
        self.data = data
        self.num_frames = len(self.data)

    def animate(self, final_frame = None):
        fig = plt.figure()
        if final_frame is None:
            final_frame = self.num_frames
        print(arange(final_frame))
        # ax = fig.add_subplot()
        animation.FuncAnimation(fig, self.create_frame, arange(final_frame), interval=15)
        plt.show() 

    # def create_frame(self, t):
    #     print(t)
    #     lat_inds, lon_inds = [pair for pair in zip(*self.data[t].index)]
    #     frame = self.blank_grid.copy()
    #     frame[lat_inds, lon_inds] += self.data[t].values
    #     ax.imshow(frame)
        # plt.show()

    def create_frame(self,t):
        x = np.linspace(0,10,100)
        plt.plot(x[t], np.sin(x[t]))

