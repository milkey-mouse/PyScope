import wireframe as wf
import numpy as np
import sys

def parseOBJ(filename):
    verts = []
    vertsOut = []
    nodes = []
    with open(filename, "r") as objfile:
        #lines = 0
        #while objfile.readline():
        #    lines += 1
        #objfile.seek(0,0)
        #readlines = 0
        for line in objfile:
            #readlines += 1
            #if readlines % 100 == 0:
                #print str(int((float(readlines) / float(lines)) * 100)) + "% complete - " + str(readlines) + "/" + str(lines)
            try:
                vals = line.split()
                if vals[0] == "v":
                    v = map(float, (i.rstrip(",") for i in vals[1:4]))
                    verts.append(v)
                if vals[0] == "f":
                    face = []
                    for f in vals[1:]:
                        w = f.split("/")
                        # OBJ Files are 1-indexed so we must subtract 1 below
                        face.append(tuple(verts[int(w[0])-1]))
                    vertsOut.append(tuple(face))
            except:
                pass
    return vertsOut

def loadOBJ(filename):
    print "Loading OBJ " + filename
    loaded_faces = parseOBJ(filename)
    edges = {}
    nodes = {}
    for face in loaded_faces:
        for edge in zip(list([face[-1]])+list(face[:-1]),face):
            edges[edge] = None
        for vertex in face:
            nodes[vertex] = None
    edge_indexes = {}
    nodes = nodes.keys()
    for edge in edges.iterkeys():
        edge_indexes[tuple(nodes.index(i) for i in edge)] = None
    edges = np.array(edge_indexes.keys())
    nodes = np.array(nodes)
    wireframe = wf.Wireframe(nodes)
    wireframe.addEdges(edges)
    return wireframe
