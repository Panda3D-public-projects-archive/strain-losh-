from direct.showbase import DirectObject
from direct.task import Task
from pandac.PandaModules import *
import math
import utils

class Combat():
    def __init__(self):
        self.beammd = MeshDrawer()
        self.beammd.setBudget(20)
        self.mdbeamgennode = self.beammd.getRoot()
        self.mdbeamgennode.reparentTo(render)
        beamtex = loader.loadTexture("beam.png")
        self.mdbeamgennode.setTexture(beamtex)
        self.mdbeamgennode.setTransparency(True)
        self.mdbeamgennode.setPos(0,0,0)
        self.mdbeamgennode.setDepthWrite(False)
        self.mdbeamgennode.setTwoSided(True)
        self.mdbeamgennode.setLightOff(True)
        self.mdbeamgennode.setBin("fixed", 100)
        self.mdbeamgennode.node().setBounds(BoundingSphere((0, 0, 0), 500))
        self.mdbeamgennode.node().setFinal(True)
        
        self.source = None
        self.target = None
        
    def drawBeam(self, task):
        t = globalClock.getFrameTime()
        task_end = False
        if task.time > 0.7:
            self.source = None
            self.target = None
            task_end= True
            
        self.beammd.begin(base.cam, render)
        # All particle drawing operations have to go here in between begin() and end()
      
        if self.source != None and self.target != None:
            # Draw the beam
            # Parameters: start position, stop position, UV coordinates, segment thickness, color
            p1 = Vec3(self.source.getX(), self.source.getY(), utils.GROUND_LEVEL + 0.5)
            p2 = Vec3(self.target.getX(), self.target.getY(), utils.GROUND_LEVEL + 0.5) 
            self.beammd.segment(p1, p2,Vec4(0,0,1.0,1.0),0.05*math.sin(t*20)+0.1,Vec4(0.2,1.0,1.0,1.0))

        self.beammd.end()
        
        if task_end == True:
            return task.done
        
        return task.cont        