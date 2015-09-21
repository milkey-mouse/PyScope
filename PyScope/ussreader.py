import struct


class USSReader:
    def __init__(self, filename):
        parsed = {}
        with open(filename) as f:
            code = compile(f.read(), filename, "exec")
            exec(code, parsed)
        resolution = int(parsed["resolution"]) if "resolution" in parsed else 96
        bps = (int(parsed["tempo"]) if "tempo" in parsed else 120) / 60
        divisor = resolution * bps
        notes = (((self.notenumbertofreq(i[0]) if i[0] is not None else None), i[1]) for i in parsed["notes"])
        self.notes = [(x[0], (x[1] / divisor if x[1] is not None else None)) for x in notes]

    def notenumbertofreq(self, notenum):
        #https://en.wikipedia.org/wiki/MIDI_Tuning_Standard
        return (2**((notenum-69)/12.0)) * 440.0
