import math


class ScopeEffect:
    """The base effect for all other effects."""

    def create(self, viewer):
        """This function will be run when the display starts."""
        pass

    def update(self, viewer):
        """This function will be run once per frame, after all of the main update functions."""
        pass

class DrawSpeedTween(ScopeEffect):
    """Starts off at one speed (fps) and ends at another. Can delay after finish and then stop automatically."""
    def __init__(self, start, end, step, finish_delay=None):
        if step == 0 and end - start != 0:
            raise Exception("Will never reach desired fps. Step is 0 when it needs to move.")
        elif not step < 0 and start - end > 0:
            raise Exception("Will never reach desired fps. Step is going the wrong direction.")
        elif not step > 0 and start - end < 0:
            raise Exception("Will never reach desired fps. Step is going the wrong direction.")
        else:
            self.fps = start
            self.start = start
            self.end = end
            self.step = step
            self.compare = max if start - end > 0 else min
            self.finish_delay = finish_delay

    def update_fps(self, viewer):
        if viewer.wavout:
            viewer.wavout.setfps(self.fps)
        viewer.fixed_dt = 1.0 / float(self.fps)

    def create(self, viewer):
        if self.finish_delay:
            viewer.time_left = None
            viewer.total_time = None
        self.update_fps(viewer)

    def update(self, viewer, dt):
        self.fps += 1
        self.fps = self.compare(self.fps, self.end)
        if self.fps == self.end and self.finish_delay:
            self.finish_delay -= dt
            if self.finish_delay <= 0:
                viewer.running = False
            else:
                print "Finishing " + str(int(math.ceil(self.finish_delay * self.fps))) + " frames"
        elif self.finish_delay:
            print "Ramping FPS: " + str(self.fps)
        self.update_fps(viewer)
