import wireframeDisplay as wd
import basicShapes as shape
import wavoutput as wav
import objparser as obj
import wireframe as wf
import effects as fx

import multiprocessing
import shutil
import errno
import sys
import os

import warnings
with warnings.catch_warnings():  # pypy's experimental version of numpy always screams at you
    warnings.simplefilter("ignore")
    import numpy as np


def run(filename, framerange=None, get_viewer=False, silent=False):
    if silent:
        real_stdout = sys.stdout
        sys.stdout = open(os.devnull,"w")
    if framerange and framerange[1] is not None:
        assert framerange[1] - framerange[0] > 0
    viewer = wd.WireframeViewer(800, run_time=(1.0 / spin_speed) * spin_times, filename=filename, show_view=False)
    setup_viewer(viewer)
    if framerange is not None:
        viewer.fast_forward(framerange[0])
        if framerange[1] is not None:
            viewer.record(framerange[1] - framerange[0])
        else:
            viewer.run()
    else:
        viewer.run()
    if silent:
        real_stdout.write("Worker for " + filename + " finished.\n")


def get_num_frames():
    viewer = wd.WireframeViewer(800, run_time=(1.0 / spin_speed) * spin_times, filename=None, show_view=False)
    setup_viewer(viewer)
    return viewer.lazycount()

spin_speed = 0.05
spin_times = 1.25
fps = 1
scene = "milkey"

concurrent = True
num_workers = 10


def setup_viewer(viewer):
    if scene == "shark":
        viewer.addEffect(fx.DrawSpeedTween(1, 45, 1, 20))
        viewer.addWireframe('spin', obj.loadOBJ("shark.obj"))
        viewer.wireframes['spin'].transform(wf.scaleMatrix(150))
    elif scene == "text":
        viewer.addEffect(fx.DrawSpeedTween(1, 150, 1, 50))
        viewer.addWireframe('spin', obj.loadOBJ("text_test.obj"))
        viewer.wireframes['spin'].transform(wf.scaleMatrix(3))
        viewer.wireframes['spin'].transform(wf.rotateZMatrix(-np.pi))
        viewer.wireframes['spin'].transform(wf.rotateYMatrix(-np.pi))
    elif scene == "watchdogs":
        viewer.addEffect(fx.DrawSpeedTween(1, 70, 1, 10))
        viewer.addWireframe('spin', obj.loadOBJ("watchdogs.obj"))
        viewer.wireframes['spin'].transform(wf.scaleMatrix(3))
        viewer.wireframes['spin'].transform(wf.rotateZMatrix(-np.pi))
        viewer.wireframes['spin'].transform(wf.rotateYMatrix(-np.pi))
    elif scene == "milkey":
        viewer.addEffect(fx.MIDIModulator("milkey.uss"))
        viewer.addWireframe('head', shape.Spheroid((0,)*3, (150,)*3, resolution=5))
        viewer.addWireframe('left_ear', shape.Spheroid((0,)*3, (75,)*3, resolution=3))
        viewer.addWireframe('right_ear', shape.Spheroid((0,)*3, (75,)*3, resolution=3))
    elif scene == "cube":
        viewer.addEffect(fx.DrawSpeedTween(1, 250, 2, 50))
        viewer.addWireframe('spin', shape.Cuboid((0,)*3, (150,)*3))
    elif scene == "sphere":
        viewer.addEffect(fx.DrawSpeedTween(0.25, 130, 0.25, 20))
        viewer.addWireframe('spin', shape.Spheroid((0,)*3, (150,)*3))
    if scene != "milkey":
        viewer.centerWireframe("spin")
    else:
        viewer.centerWireframe("head")
        viewer.centerWireframe("left_ear")
        viewer.wireframes["left_ear"].transform(wf.translationMatrix(150, -150, 0))
        viewer.centerWireframe("right_ear")
        viewer.wireframes["right_ear"].transform(wf.translationMatrix(-150, -150, 0))
    viewer.key_to_function = {}
    viewer.object_update = object_update

def object_update(self, dt):
    if scene == "milkey":
        self.wireframes['head'].transform(wf.rotateAboutVector(self.wireframes['head'].findCenter(), (0,1,0), np.pi * 2 * spin_speed * dt))
        self.wireframes['left_ear'].transform(wf.rotateAboutVector(self.wireframes['head'].findCenter(), (0,1,0), np.pi * 2 * spin_speed * dt))
        self.wireframes['right_ear'].transform(wf.rotateAboutVector(self.wireframes['head'].findCenter(), (0,1,0), np.pi * 2 * spin_speed * dt))
    else:
        self.wireframes['spin'].transform(wf.rotateAboutVector(self.wireframes['spin'].findCenter(), (0,1,0), np.pi * 2 * spin_speed * dt))

if __name__ == '__main__':
    if concurrent:
        total_frames = get_num_frames()
        print "Dividing workload among workers..."
        fpw = int(total_frames / num_workers)
        frameranges = []
        start = 0
        for i in range(num_workers):
            end = start + fpw
            frameranges.append((start, end))
            start = end + 1
        frameranges[-1] = (frameranges[-1][0], None)
        frameprocesses = []
        try:
            shutil.rmtree("./temp/")
            while os.path.isdir("./temp/"):
                pass
        except:
            pass
        try:
            os.makedirs("./temp/")
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        print "Running workers..."
        for i, frange in enumerate(frameranges):
            mp = multiprocessing.Process(target=run, args=("temp/" + str(i) + ".raw", frange, False, True))
            mp.start()
            frameprocesses.append(mp)
        while frameprocesses != []:
            for proc in frameprocesses:
                if not proc.is_alive():
                    proc.join()
                    frameprocesses.remove(proc)
        print "Stitching temp files together..."
        final_wav = wav.WavOutput("oscilloscope\data\konichiwa.wav", 60)
        for i in range(len(frameranges)):
            filepath = "./temp/" + str(i) + ".raw"
            print filepath[2:]
            with open(filepath, "rb") as rawdata:
                while True:
                    buf = rawdata.read(8192)
                    if not buf:
                        break
                    final_wav.buffer_wav(buf)
        final_wav.buffer_wav(None)
        print "Done!"
        try:
            shutil.rmtree("./temp/")
        except:
            pass
    else:
        run("oscilloscope\data\konichiwa.wav")