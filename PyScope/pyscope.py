import wireframeDisplay as wd
import basicShapes as shape
import objparser as obj
import wireframe as wf
import effects as fx

from multiprocessing import Pool
import numpy as np
import itertools
import struct
import math
import time
import wave
import sys


def object_update(self, dt):
    self.wireframes['spin'].transform(wf.rotateAboutVector(self.wireframes['spin'].findCenter(), (0,1,0), np.pi * 2 * spin_speed * dt))


def setup_viewer(viewer):
    viewer.addEffect(fx.DrawSpeedTween(1, 250, 2, 4))
    scene = "text"
    if scene == "shark":
        viewer.addWireframe('spin', obj.loadOBJ("shark.obj"))
        viewer.wireframes['spin'].transform(wf.scaleMatrix(150))
    elif scene == "text":
        viewer.addWireframe('spin', obj.loadOBJ("text_test.obj"))
        viewer.wireframes['spin'].transform(wf.scaleMatrix(3))
        viewer.wireframes['spin'].transform(wf.rotateZMatrix(-np.pi))
        viewer.wireframes['spin'].transform(wf.rotateYMatrix(-np.pi))
    elif scene == "cube":
        viewer.addWireframe('spin', shape.Cuboid((0,)*3, (150,)*3))
    viewer.centerWireframe("spin")
    viewer.key_to_function = {}
    viewer.object_update = object_update


def run(filename, framerange=None, get_viewer=False):
    if framerange:
        assert framerange[1] - framerange[0] > 0
    viewer = wd.WireframeViewer(800, run_time=(1.0 / spin_speed) * spin_times, filename=filename)
    setup_viewer(viewer)
    if framerange is not None:
        viewer.fast_forward(framerange[0])
        viewer.record(framerange[1] - framerange[0])
    else:
        viewer.run()

if __name__ == '__main__':
    spin_speed = 0.05
    spin_times = 1.25
    fps = 1
    run("oscilloscope\data\konichiwa.wav", framerange=(100,110))