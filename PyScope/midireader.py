import struct
import midi


class MidiReader:
    def __init__(self, filename):
        parsed = midi.read_midifile(filename)
        parsed.make_ticks_abs()
        self.track = []
        last_track = None
        time_signature = 4.0
        bpm = 120.0
        for track in parsed:
            for item in track:
                if type(item) is midi.SetTempoEvent:
                    # midi is stupid
                    bps = round(60000000.0/int(hex(item.data[0])[2:]+hex(item.data[1])[2:]+hex(item.data[2])[2:], 16)) / 60.0
                elif type(item) is midi.TimeSignatureEvent:
                    time_signature = float(item.data[0])
                elif type(item) is midi.NoteOnEvent:
                    if item.data[1] == 0:  # equivalent to NoteOffEvent
                        continue
                    last_track = track
                    self.track.append((item.tick, self.notenumbertofreq(item.data[0])))
        # get the last note and end it at the right time
        for item in last_track[::-1]:
            if type(item) is midi.NoteOnEvent:
                if item.data[1] == 0:
                    self.track.append((item.tick, None))
                    break
            elif type(item) is midi.NoteOffEvent:
                self.track.append((item.tick, None))
                break
        self.notes = sorted(list(set(self.track)), key=(lambda x: x[0]))  #remove duplicates and ensure sort order
        self.notes = [(x[0] / parsed.resolution / bps, x[1]) for x in self.notes]  #convert to seconds
        print self.notes

    def notenumbertofreq(self, notenum):
        # https://en.wikipedia.org/wiki/MIDI_Tuning_Standard
        return (2.0**((notenum-69)/12.0)) * 440.0
