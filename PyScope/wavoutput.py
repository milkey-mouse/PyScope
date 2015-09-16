import itertools
import struct
import math
import wave


class WavOutput:
    """Outputs a list of vectors to a wav file."""

    def __init__(self, filename, fps, rate=192000):
        self.wavrange = 32766
        self.chunk_size = 1024 * 1024 # 1 MB
        self.wavbuffer = []
        self.samples_per_frame = rate / fps
        self.samplerate = rate

        self.audio_out = wave.open(filename, 'w')
        self.audio_out.setparams((2, 2, rate, 0, 'NONE', 'not compressed'))

    @property
    def fps(self):
        """Updating this updates the number of samples per frame"""
        return None

    @fps.setter
    def fps(self, value):
        self.samples_per_frame = self.samplerate / value

    def distance(self, p0, p1):
        """Get distance between two 2D points."""
        return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)

    def valid_vecs(self, vecs, size):
        """Returns only non-duplicate vectors, shrunken to within wavrange"""
        results = set()
        shrunken = set()
        for vec in vecs:
            if (vec not in results) and (vec[::-1] not in results):
                results.add(vec)
                if abs(vec[0][0]) > size or abs(vec[0][1]) > size or abs(vec[1][0]) > size or abs(vec[1][1]) > size:
                    continue
                shrunken.add(((((vec[0][0] / size) * self.wavrange * 2) - self.wavrange, ((vec[0][1] / size) * self.wavrange * 2) - self.wavrange), (((vec[1][0] / size) * self.wavrange * 2) - self.wavrange, ((vec[1][1] / size) * self.wavrange * 2) - self.wavrange)))
        return shrunken

    def buffer_wav(self, chunk):
        if chunk is None:
            self.audio_out.writeframes("".join(self.wavbuffer))
            self.audio_out.close()
            del self.wavbuffer[:]
            return
        self.wavbuffer.append(chunk)
        if len(self.wavbuffer) > self.chunk_size:
            self.audio_out.writeframes("".join(self.wavbuffer))
            del self.wavbuffer[:]  # insta-clear with GC'

    def add_sample(self, vec):
        try:
            left = struct.pack('h', int(round(vec[0])))
            right = struct.pack('h', int(round(vec[1])))
            self.buffer_wav(left)
            self.buffer_wav(right)
        except:
            pass

    def wavify(self, unsorted_vecs, size):
        vecs = self.valid_vecs(unsorted_vecs, size)
        distances = {}
        for vec in vecs:
            distances[vec] = self.distance(vec[0], vec[1])
        drawspeed = sum(distances.itervalues()) / self.samples_per_frame
        offset = -0.1
        step = 0.01
        samples = {}
        while True:
            samples_left = int(self.samples_per_frame)
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
                self.add_sample(pos)
        for _ in range(samples_left):
            self.add_sample((0,0))