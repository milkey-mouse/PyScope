import warnings
with warnings.catch_warnings():  # pypy's experimental version of numpy always screams at you
    warnings.simplefilter("ignore")
    import numpy as np
import effects as fx
import wireframe as wf
import wavoutput as wav

import time
import sys
import os


class WireframeViewer(wf.WireframeGroup):
    """A group of wireframes which can be displayed on a Pygame screen or obtained as a list of 2D vectors."""

    def __init__(self, size, name="PyScope", line_width=3, fps=None, show_view=("PyPy" not in sys.version), \
                 run_time=1.0, filename=None):
        self.size = size
        self.width = size
        self.height = size

        self.time_left = run_time
        self.total_time = run_time
        self.last_percent = 0.0
        self.has_run = False

        if show_view:
            import pygame
            self.screen = pygame.display.set_mode((size,) * 2)
            pygame.display.set_caption(name)
            self.timer = pygame.time.Clock()

        if filename:
            if fps:
                self.wavout = wav.WavOutput(filename=filename, fps=fps)
            else:
                self.wavout = wav.WavOutput(filename=filename, fps=60)
                print "Warning: No FPS provided! Unless you're modifying it with an effect, please set the FPS on init."
        else:
            self.wavout = None
        
        self.wireframes = {}
        self.effects = []
        self.object_to_update = []
        
        self.perspective = 500.0
        self.eyeX = self.width/2
        self.eyeY = 100
        self.view_vector = np.array([0, 0, -1])
        
        self.background = (0,0,0)
        self.nodeColour = (0,180,255)
        self.line_width = line_width
        self.fixed_dt = fps
        if self.fixed_dt is not None:
            self.fixed_dt = 1.0 / float(self.fixed_dt)
        self.show_view = show_view

        self.start_time = time.time()
        self.lastdelta = 0

        if show_view:
            self.rotation_amount = np.pi/32
            self.movement_amount = 5
            self.key_to_function = {
                pygame.K_LEFT:   (lambda x: x.transform(wf.translationMatrix(dx=-self.movement_amount))),
                pygame.K_RIGHT:  (lambda x: x.transform(wf.translationMatrix(dx= self.movement_amount))),
                pygame.K_UP:     (lambda x: x.transform(wf.translationMatrix(dy=-self.movement_amount))),
                pygame.K_DOWN:   (lambda x: x.transform(wf.translationMatrix(dy= self.movement_amount))),
                pygame.K_EQUALS: (lambda x: x.scale(1.25)),
                pygame.K_MINUS:  (lambda x: x.scale(0.8)),
                pygame.K_q:      (lambda x: x.rotate('x', self.rotation_amount)),
                pygame.K_w:      (lambda x: x.rotate('x',-self.rotation_amount)),
                pygame.K_a:      (lambda x: x.rotate('y', self.rotation_amount)),
                pygame.K_s:      (lambda x: x.rotate('y',-self.rotation_amount)),
                pygame.K_z:      (lambda x: x.rotate('z', self.rotation_amount)),
                pygame.K_x:      (lambda x: x.rotate('z',-self.rotation_amount))
            }
        else:
            self.key_to_function = {}

        self.frame_vectors = []

    def addEffect(self, effect):
        """Add a new instance of a ScopeEffect derivative to the active effects"""
        if not isinstance(effect, fx.ScopeEffect):
            raise Exception("Not a derivative of effects.ScopeEffect.")
        else:
            self.effects.append(effect)

    def removeEffect(self, effect_class):
        to_delete = []
        for effect in self.effects:
            if isinstance(effect, effect_class):
                to_delete.append(effect)
        for effect in to_delete:
            self.effects.remove(effect)
        
    def centerWireframe(self, name, z=0):
        target = self.wireframes[name]
        center_translate = np.negative(target.findCenter()) + np.array([(self.size / 2), (self.size / 2), z])
        target.transform(wf.translationMatrix(center_translate[0], center_translate[1], center_translate[2]))

    def addWireframe(self, name, wireframe):
        self.wireframes[name] = wireframe
    
    def addWireframeGroup(self, wireframe_group):
        # Potential danger of overwriting names
        for name, wireframe in wireframe_group.wireframes.items():
            self.addWireframe(name, wireframe)
    
    def scale(self, scale):
        """Scale wireframes in all directions from the center of the group"""
        scale_matrix = wf.scaleMatrix(scale, self.width/2, self.height/2, 0)
        self.transform(scale_matrix)

    def rotate(self, axis, amount):
        """Rotate the "camera" by rotating all other wireframes"""
        (x, y, z) = self.findCenter()
        translation_matrix1 = wf.translationMatrix(-x, -y, -z)
        translation_matrix2 = wf.translationMatrix(x, y, z)

        axis = axis.lower()

        if axis == 'x':
            rotation_matrix = wf.rotateXMatrix(amount)
        elif axis == 'y':
            rotation_matrix = wf.rotateYMatrix(amount)
        elif axis == 'z':
            rotation_matrix = wf.rotateZMatrix(amount)
        else:
            raise Exception("Invalid rotation axis. Valid axes are x, y, and z.")

        rotation_matrix = np.dot(np.dot(translation_matrix1, rotation_matrix), translation_matrix2)
        self.transform(rotation_matrix)

    def display(self):
        self.frame_vectors = []

        if self.show_view:
            self.screen.fill(self.background)
        
        for name, wireframe in self.wireframes.iteritems():
            nodes = wireframe.nodes

            for (n1, n2) in wireframe.edges:
                if self.perspective:
                    if wireframe.nodes[n1][2] > -self.perspective and nodes[n2][2] > -self.perspective:
                        z1 = self.perspective/ (self.perspective + nodes[n1][2])
                        x1 = self.width/2  + z1*(nodes[n1][0] - self.width/2)
                        y1 = self.height/2 + z1*(nodes[n1][1] - self.height/2)

                        z2 = self.perspective/ (self.perspective + nodes[n2][2])
                        x2 = self.width/2  + z2*(nodes[n2][0] - self.width/2)
                        y2 = self.height/2 + z2*(nodes[n2][1] - self.height/2)

                        self.frame_vectors.append(((x1, y1), (x2, y2)))
                        if self.show_view:
                            pygame.draw.line(self.screen, self.nodeColour, (x1, y1), (x2, y2), self.line_width)
                else:
                    self.frame_vectors.append(((nodes[n1][0], nodes[n1][1]), (nodes[n2][0], nodes[n2][1])))
                    if self.show_view:
                        pygame.draw.line(self.screen, self.nodeColour, (nodes[n1][0], nodes[n1][1]), (nodes[n2][0], nodes[n2][1]), self.line_width)

        if self.show_view:
            pygame.display.flip()

    def keyEvent(self, key):
        if key in self.key_to_function:
            self.key_to_function[key](self)

    def getdelta(self):
        if self.fixed_dt is not None:
            return self.fixed_dt
        elif self.show_view:
            dt = pygame.time.get_ticks() - self.lastdelta
            self.lastdelta += dt
            return float(dt) / 1000.0

    def frame_update(self, _, dt):
        if self.time_left is None:
            return
        self.time_left -= dt
        percent = round(((self.total_time - self.time_left) / self.total_time) * 100, 1)
        if self.last_percent != percent:
            self.last_percent = percent
            print str(percent) + "% finished rendering"
        if self.time_left <= 0:
            self.running = False
            return

    def audio_update(self, _):
        if self.wavout:
            self.wavout.wavify(self.frame_vectors, self.width)

    def lazycount(self):
        """Run nothing but the frame counter, then reset."""
        wireframes_tmp = self.wireframes
        print "Lazy-counting frames..."
        real_stdout = sys.stdout
        sys.stdout = open(os.devnull,"w")
        for effect in self.effects:
            effect.create(self)
        self.running = True
        tmp = self.show_view
        self.show_view = False
        i = 0
        while self.running:
            dt = self.getdelta()
            self.frame_update(self, dt)
            for effect in self.effects:
                effect.update(self, dt)
            i += 1
        print str(i) + " frames total."
        self.running = False
        self.show_view = tmp
        self.wireframes = wireframes_tmp
        sys.stdout = real_stdout
        return i


    def fast_forward(self, frames):  # somewhat hacky
        """Run the main loop, without export, for a certain number of frames."""
        print "Fast-forwarding " + str(frames) + " frames..."
        real_stdout = sys.stdout
        sys.stdout = open(os.devnull,"w")
        if not self.has_run:
            for effect in self.effects:
                effect.create(self)
        self.has_run = True
        self.running = True
        tmp = self.show_view
        self.show_view = False
        for i in xrange(frames):
            #if i % 10 == 9:
            #    print str(i + 1) + "/" + str(frames)
            self.display()
            dt = self.getdelta()
            self.object_update(self, dt)
            for effect in self.effects:
                effect.update(self, dt)
        self.running = False
        self.show_view = tmp
        sys.stdout = real_stdout

    def record(self, frames, view=False):  # somewhat hacky
        """Run the main loop, with export, for a certain number of frames."""
        print "Recording " + str(frames) + " frames..."
        if not self.has_run:
            for effect in self.effects:
                effect.create(self)
        self.has_run = True
        self.running = True
        tmp = self.show_view
        self.show_view = view
        for i in xrange(frames):
            if i % 10 == 9:
                print str(i + 1) + "/" + str(frames)
            self.display()
            dt = self.getdelta()
            self.object_update(self, dt)
            self.audio_update(self)
            self.frame_update(self, dt)
            for effect in self.effects:
                effect.update(self, dt)
        self.running = False
        self.show_view = tmp

        if self.wavout:
            self.wavout.buffer_wav(None)  # flush buffer

    def run(self):
        """Display wireframe on screen and respond to keydown events"""
        if not self.has_run:
            for effect in self.effects:
                effect.create(self)
        self.has_run = True
        """Display wireframe on screen and respond to keydown events"""
        for effect in self.effects:
            effect.create(self)
        self.running = True
        while self.running:
            if self.show_view:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        key_down = event.key
                    elif event.type == pygame.KEYUP:
                        key_down = None
                if key_down:
                    self.keyEvent(key_down)
            self.display()
            dt = self.getdelta()
            self.object_update(self, dt)
            self.audio_update(self)
            self.frame_update(self, dt)
            for effect in self.effects:
                effect.update(self, dt)

        if self.show_view:
            pygame.quit()
        if self.wavout:
            self.wavout.buffer_wav(None)  # flush buffer