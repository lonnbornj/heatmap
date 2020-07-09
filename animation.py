import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from numpy import arange
import numpy as np



x = np.linspace(0,8*np.pi,1000)
y = np.sin(x)

fig = plt.figure()
ax = plt.axes()

class Animation:
    def __init__(self, blank_grid, data):
        self.blank_grid = blank_grid
        self.data = data
        self.num_frames = len(self.data)

    def animate(self, final_frame = None):
        if final_frame is None:
            final_frame = self.num_frames
        # ax = fig.add_subplot()
        anim = animation.FuncAnimation(fig, self.create_frame, arange(final_frame), interval=1)
        plt.show() 

    def create_frame(self, t):
        lat_inds, lon_inds = [pair for pair in zip(*self.data[t].index)]
        frame = self.blank_grid.copy()
        frame[lat_inds, lon_inds] += self.data[t].values
        ax.clear()
        ax.imshow(frame)

    # def create_frame(self,t):
    #     ax.clear()
    #     ax.plot(x[0:t], np.sin(x[0:t]))
    #     ax.set_xlim(0, x[-1])
    #     ax.set_ylim([-1.1,1.1])

# a=animation.FuncAnimation(fig, a.create_frame, arange(len(x)), interval=200)

# plt.show()