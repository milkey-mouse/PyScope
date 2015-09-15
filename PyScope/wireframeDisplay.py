import numpy as np
import wireframe as wf

class WireframeViewer(wf.WireframeGroup):
    """ A group of wireframes which can be displayed on a Pygame screen """
    
    def __init__(self, width, height, name="Wireframe Viewer", line_width=1, frame_limit=None, fixed_dt=None, show_view=True):
        self.width = width
        self.height = height

        if show_view:
            import pygame
            self.screen = pygame.display.set_mode((width, height))
            pygame.display.set_caption(name)
            self.timer = pygame.time.Clock()
        
        self.wireframes = {}
        self.wireframe_colours = {}
        self.object_to_update = []
        
        self.displayNodes = False
        self.displayEdges = True
        self.displayFaces = True
        
        self.perspective = False # 300.
        self.eyeX = self.width/2
        self.eyeY = 100
        self.view_vector = np.array([0, 0, -1])
        
        self.background = (10,10,50)
        self.nodeColour = (250,250,250)
        self.line_width = line_width
        self.frame_limit = frame_limit
        self.fixed_dt = fixed_dt
        if self.fixed_dt is not None:
            self.fixed_dt = 1.0 / float(self.fixed_dt)
        self.nodeRadius = self.line_width
        self.show_view = show_view
        
        self.control = 0
        
        self.rotation_amount = np.pi/32
        self.movement_amount = 5

        self.lastdelta = 0

        if show_view:
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

    def addWireframe(self, name, wireframe):
        self.wireframes[name] = wireframe
        #   If colour is set to None, then wireframe is not displayed
        self.wireframe_colours[name] = (250,250,250)
    
    def addWireframeGroup(self, wireframe_group):
        # Potential danger of overwriting names
        for name, wireframe in wireframe_group.wireframes.items():
            self.addWireframe(name, wireframe)
    
    def scale(self, scale):
        """ Scale wireframes in all directions from the centre of the group. """
        
        scale_matrix = wf.scaleMatrix(scale, self.width/2, self.height/2, 0)
        self.transform(scale_matrix)

    def rotate(self, axis, amount):
        (x, y, z) = self.findCentre()
        translation_matrix1 = wf.translationMatrix(-x, -y, -z)
        translation_matrix2 = wf.translationMatrix(x, y, z)
        
        if axis == 'x':
            rotation_matrix = wf.rotateXMatrix(amount)
        elif axis == 'y':
            rotation_matrix = wf.rotateYMatrix(amount)
        elif axis == 'z':
            rotation_matrix = wf.rotateZMatrix(amount)
            
        rotation_matrix = np.dot(np.dot(translation_matrix1, rotation_matrix), translation_matrix2)
        self.transform(rotation_matrix)

    def display(self):
        if self.frame_limit is not None:
            self.timer.tick(self.frame_limit)
        self.frame_vectors = []

        if self.show_view:
            self.screen.fill(self.background)
        
        for name, wireframe in self.wireframes.iteritems():
            nodes = wireframe.nodes

            if self.displayEdges:
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

            if self.show_view and self.displayNodes:
                for node in nodes:
                    pygame.draw.circle(self.screen, self.nodeColour, (int(node[0]), int(node[1])), self.nodeRadius, 0)

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

    def run(self):
        """ Display wireframe on screen and respond to keydown events """
        
        self.running = True
        key_down = False
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
            self.update(self, self.getdelta())

        if self.show_view:
            pygame.quit()