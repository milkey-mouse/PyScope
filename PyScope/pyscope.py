import wireframeDisplay as wd
import basicShapes as shape
import objparser as obj
import wireframe as wf
import numpy as np
import itertools
import struct
import math
import time
import wave
import sys

spin_speed = 0.05

spin_times = 1.25

chunk_size = 1024 * 1024 # 1 MB

wavbuffer = []

fps = 1

audio_out = wave.open('oscilloscope\data\konichiwa.wav', 'w')
audio_out.setparams((2, 2, 192000, 0, 'NONE', 'not compressed'))
wavrange = 32766
samples_per_frame = 192000 / fps
time_left = (1.0 / spin_speed) * spin_times


def distance(p0, p1):
    return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)


def buffer_wav(chunk):
    if chunk is None:
        audio_out.writeframes("".join(wavbuffer))
        audio_out.close()
        del wavbuffer[:]
        return
    wavbuffer.append(chunk)
    if len(wavbuffer) > chunk_size:
        audio_out.writeframes("".join(wavbuffer))
        del wavbuffer[:]  # insta-clear with GC'


def add_sample(vec):
    try:
        left = struct.pack('h', int(round(vec[0])))
        right = struct.pack('h', int(round(vec[1])))
        buffer_wav(left)
        buffer_wav(right)
    except:
        pass


def wavify(vecs):
    distances = {}
    for vec in vecs:
        distances[vec] = distance(vec[0], vec[1])
    drawspeed = sum(distances.itervalues()) / samples_per_frame
    offset = -0.1
    step = 0.01
    samples = {}
    while True:
        samples_left = int(samples_per_frame)
        for vec in vecs:
            start = vec[0]
            end = vec[1]
            vec_samples = int(round((distances[vec] / drawspeed) - offset))
            samples[vec] = vec_samples
            samples_left -= vec_samples
        if samples_left >= 0:
            break
        samples = {}
        offset += step
    keys = samples.keys()
    keys.sort(key=lambda pt: ((pt[0][0] + pt[1][0]) / 2, (pt[0][1] + pt[1][1]) / 2))
    for vec, vec_samples in itertools.izip(keys, itertools.imap(samples.get, keys)):
        pos = list(vec[0])
        dist = distances[vec]
        normal = ((vec[1][0] - vec[0][0]) / (vec_samples - 1), (vec[1][1] - vec[0][1]) / (vec_samples - 1))
        for i in xrange(vec_samples - 1):
            pos[0] += normal[0]
            pos[1] += normal[1]
            add_sample(pos)
    for _ in range(samples_left):
        add_sample((0,0))


def valid_vecs(vecs, size):
    results = set()
    shrunken = set()
    for vec in vecs:
        if (vec not in results) and (vec[::-1] not in results):
            results.add(vec)
            if abs(vec[0][0]) > size or abs(vec[0][1]) > size or abs(vec[1][0]) > size or abs(vec[1][1]) > size:
                continue
            shrunken.add(((((vec[0][0] / size) * wavrange * 2) - wavrange, ((vec[0][1] / size) * wavrange * 2) - wavrange), (((vec[1][0] / size) * wavrange * 2) - wavrange, ((vec[1][1] / size) * wavrange * 2) - wavrange)))
    return shrunken

def scope_update(self, dt):
    global samples_per_frame
    self.time_left -= dt
    percent = round(((self.total_time - self.time_left) / self.total_time) * 100, 1)
    if self.last_percent != percent:
        self.last_percent = percent
        print str(percent) + "% finished rendering"
    if self.time_left <= 0:
        self.running = False
        return
    self.wireframes['text'].transform(wf.rotateAboutVector(self.wireframes['text'].findCentre(), (0,1,0), np.pi * 2 * spin_speed * dt))
    #self.wireframes['shark'].transform(wf.rotateAboutVector(self.wireframes['shark'].findCentre(), (0,1,0), -(np.pi * 2 * spin_speed * dt) / 2))
    wavify(valid_vecs(self.frame_vectors, float(self.width)))
    #valid_vecs(self.frame_vectors, float(self.width))
    if self.fps < 100.0:
        self.fps += 1
        samples_per_frame = 192000 / self.fps
        self.fixed_dt = 1.0 / float(self.fps)
        #print self.fps


viewer = wd.WireframeViewer(800, 800, "PyScope", line_width=3, fixed_dt=fps, show_view=("PyPy" not in sys.version))
viewer.fps = fps
viewer.time_left = time_left
viewer.total_time = time_left
viewer.last_percent = 0.0
#viewer.addWireframe('text', shape.Cuboid((0, 0, 0), (100, 100, 100)))
viewer.addWireframe('text', obj.loadOBJ("text_test.obj"))
#viewer.addWireframe('text', obj.loadOBJ("shark.obj"))
#viewer.wireframes['text'].transform(wf.scaleMatrix(150))
viewer.wireframes['text'].transform(wf.scaleMatrix(3))
viewer.wireframes['text'].transform(wf.rotateZMatrix(-np.pi))
viewer.wireframes['text'].transform(wf.rotateYMatrix(-np.pi))
centerTranslate = np.negative(viewer.wireframes['text'].findCentre()) + np.array([(viewer.width / 2), (viewer.height / 2), 0])
viewer.wireframes['text'].transform(wf.translationMatrix(centerTranslate[0], centerTranslate[1], centerTranslate[2]))
#viewer.wireframes['text'].transform(wf.translationMatrix(0, 100, 0))
#viewer.addWireframe('shark', obj.loadOBJ("shark.obj"))
#viewer.wireframes['shark'].transform(wf.scaleMatrix(100))
#viewer.wireframes['shark'].transform(wf.rotateXMatrix(np.pi))
#centerTranslate = np.negative(viewer.wireframes['shark'].findCentre()) + np.array([(viewer.width / 2), (viewer.height / 2), 0])
#viewer.wireframes['shark'].transform(wf.translationMatrix(centerTranslate[0], centerTranslate[1], centerTranslate[2]))
#viewer.wireframes['shark'].transform(wf.translationMatrix(0, -100, 0))
viewer.displayFaces = False
viewer.displayEdges = True
viewer.displayNodes = False
viewer.background = (0,0,0)
viewer.nodeColour = (0,180,255)
viewer.nodeRadius = 2
viewer.perspective = 500
viewer.key_to_function = {}
viewer.update = scope_update
viewer.start_time = time.time()
viewer.run()
buffer_wav(None)