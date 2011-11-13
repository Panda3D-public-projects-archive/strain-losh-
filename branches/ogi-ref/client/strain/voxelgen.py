#############################################################################
# IMPORTS
#############################################################################

# python imports

# panda3D imports
from pandac.PandaModules import GeomNode, NodePath, GeomVertexFormat, GeomVertexData, Geom, GeomVertexWriter, GeomTristrips, Vec3
from panda3d.core import Texture, GeomNode
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomTriangles, GeomVertexWriter
from panda3d.core import Vec3, Vec4, Point3
import time

# strain related imports
import strain.utils as utils
 
#############################################################################
# METHODS
#############################################################################

class VoxelGenerator():
    def __init__(self, name, size, height):        
        self.name = name
        self.finished = False
        self.size = size
        self.height = height

        self.format = GeomVertexFormat.getV3n3c4t2()
        self.vertexData = GeomVertexData(name, self.format, Geom.UHStatic)
        
        self.mesh = Geom(self.vertexData)
        self.triangles = GeomTriangles(Geom.UHStatic)
        self.triangleData = self.triangles.modifyVertices()
        
        self.vertex = GeomVertexWriter(self.vertexData, 'vertex')
        self.normal = GeomVertexWriter(self.vertexData, 'normal')
        self.color = GeomVertexWriter(self.vertexData, 'color')
        self.texcoord = GeomVertexWriter(self.vertexData, 'texcoord')
        
        self.faceCount = 0
    
    def makeFace(self, x1, y1, z1, x2, y2, z2, id, color):
        
        # Populate vertex array
        if x1 != x2:
            self.vertex.addData3f(x1, y1, z1)
            self.vertex.addData3f(x2, y1, z1)
            self.vertex.addData3f(x2, y2, z2)
            self.vertex.addData3f(x1, y2, z2)
            
            # Populate normal array
            e1 = Vec3(Point3(x2, y1, z1) - Point3(x1, y1, z1))
            e2 = Vec3(Point3(x2, y2, z2) - Point3(x2, y1, z1))
            n = e1.cross(e2)
            n = utils.normalize(n)      
            self.normal.addData3f(n.getX(), n.getY(), n.getZ())
            self.normal.addData3f(n.getX(), n.getY(), n.getZ())
            self.normal.addData3f(n.getX(), n.getY(), n.getZ())
            self.normal.addData3f(n.getX(), n.getY(), n.getZ())
                  
        else:
            self.vertex.addData3f(x1, y1, z1)
            self.vertex.addData3f(x2, y2, z1)
            self.vertex.addData3f(x2, y2, z2)
            self.vertex.addData3f(x1, y1, z2)
            
            # Populate normal array
            e1 = Vec3(Point3(x2, y2, z1) - Point3(x1, y1, z1))
            e2 = Vec3(Point3(x2, y2, z2) - Point3(x2, y1, z1))
            n = e1.cross(e2)
            n = utils.normalize(n)      
            self.normal.addData3f(n.getX(), n.getY(), n.getZ())
            self.normal.addData3f(n.getX(), n.getY(), n.getZ())
            self.normal.addData3f(n.getX(), n.getY(), n.getZ())
            self.normal.addData3f(n.getX(), n.getY(), n.getZ())        


        # Populate color array
        self.color.addData4f(color, color, color, 1.0)
        self.color.addData4f(color, color, color, 1.0)
        self.color.addData4f(color, color, color, 1.0)
        self.color.addData4f(color, color, color, 1.0)
        
        # Populate texcoord array
        """
        self.texcoord.addData2f(0.0, 1.0)
        self.texcoord.addData2f(0.0, 0.0)
        self.texcoord.addData2f(1.0, 0.0)
        self.texcoord.addData2f(1.0, 1.0)
        """
        if id == 1:
            self.texcoord.addData2f(0.0, 1.0)
            self.texcoord.addData2f(0.0, 0.0)
            self.texcoord.addData2f(0.5, 0.0)
            self.texcoord.addData2f(0.5, 1.0)
        elif id == 2:
            self.texcoord.addData2f(0.5, 1.0)
            self.texcoord.addData2f(0.5, 0.0)
            self.texcoord.addData2f(1.0, 0.0)
            self.texcoord.addData2f(1.0, 1.0)
        
        vertexId = self.faceCount * 4
        
        self.triangles.addVertices(vertexId, vertexId + 1, vertexId + 3)
        self.triangles.addVertices(vertexId + 1, vertexId + 2, vertexId + 3)
        
        self.faceCount += 1
    
    def makeFrontFace(self, x, y, z, id):
        z = z * self.height
        self.makeFace(x + self.size, y + self.size, z, x, y + self.size, z + self.height, id, 0.6)
    
    def makeBackFace(self, x, y, z, id):
        z = z * self.height
        self.makeFace(x, y, z, x + self.size, y, z + self.height, id, 0.85)
    
    def makeRightFace(self, x, y, z, id):
        z = z * self.height
        self.makeFace(x + self.size, y, z, x + self.size, y + self.size, z + self.height, id, 1.0)
    
    def makeLeftFace(self, x, y, z, id):
        z = z * self.height
        self.makeFace(x, y + self.size, z, x, y, z + self.height, id, 0.9)
    
    def makeTopFace(self, x, y, z, id):
        z = z * self.height
        self.makeFace(x + self.size, y + self.size, z + self.height, x, y, z + self.height, id, 1.0)
    
    def makeBottomFace(self, x, y, z, id):
        z = z * self.height
        self.makeFace(x, y + self.size, z, x + self.size, y, z, id, 0.70)
    
    def getMesh(self):
        return self.mesh
    
    def getGeomNode(self):
        if self.finished == False:
            self.triangles.closePrimitive()
            self.mesh.addPrimitive(self.triangles)
            self.finished = True
        geomNode = GeomNode(self.name)
        geomNode.addGeom(self.mesh)
        return geomNode
