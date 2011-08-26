from direct.showbase import DirectObject
from panda3d.core import Plane, Vec3, Point3, Point2
from pandac.PandaModules import CollisionTraverser, CollisionHandlerQueue, CollisionNode, CollisionRay
from pandac.PandaModules import GeomNode, CardMaker
from math import floor, sin, cos, tan, radians

class clCameraHandler(DirectObject.DirectObject): 
    def __init__(self, tupCameraPos=(0, 0, 45), tupCameraDir=(0, -90, 0),  tupThetaLimit=(5, 90), booDebug=False): 

        base.disableMouse()

        # Gives the camera an initial position and rotation. 
        self.booDebug = booDebug 
        self.booOrbiting = False 
        self.booDragPanning = False 
        self.fEdgeBound = 0.95 
        self.fLastMouseX, self.fLastMouseY = 0, 0 
        self.fDragPanRate = 30 
        self.fPanRate = 0.08
        self.fPhiRate = 100 
        self.fThetaRate = 35 
        self.fZoomRate = 1.3 
        
        self.tupCurrentCameraPos = tupCameraPos 
        self.tupCurrentCameraDir = tupCameraDir 
        self.tupInitCameraDir = tupCameraDir 
        self.tupInitCameraPos = tupCameraPos 
        self.tupThetaLimit = tupThetaLimit 

        if not self.booDebug: 
            self.accept("mouse3", self.StartCameraOrbit) 
            self.accept("mouse3-up", self.StopCameraOrbit) 
            self.accept("wheel_down", self.ZoomCameraOut) 
            self.accept("wheel_up", self.ZoomCameraIn) 
            self.accept("shift-mouse1", self.StartDragPan) 
            self.accept("mouse1-up", self.StopDragPan) 
            taskMgr.add(self.CamTask,'CamTask') 
            self.GoHome() 

    def CamTask(self, task): 
        if base.mouseWatcherNode.hasMouse(): 
            mpos = base.mouseWatcherNode.getMouse() 
            t_mpos_x = mpos.getX() 
            t_mpos_y = mpos.getY() 
          
            if (self.booOrbiting): 
                self.DoOrbit(t_mpos_x, t_mpos_y) 
                return task.cont 
             
            if (self.booDragPanning): 
                self.DoDragPan(t_mpos_x, t_mpos_y) 
                return task.cont 

            if (t_mpos_x < -0.9) | (t_mpos_x > 0.9) | (t_mpos_y < -0.9) | (t_mpos_y > 0.9): 
                #If i'm making a selection, don't pan the camera. It's very annoying. 
                try: 
                    if objSelectionTool.booSelecting: 
                        return task.cont 
                except:
                    pass 
                self.DoEdgePan(t_mpos_x, t_mpos_y) 
                return task.cont 
        return task.cont 

    def DoEdgePan(self, fMX, fMY):   #MX, MY: mouse x, mouse y 
        dx, dy = 0, 0 
        old_Phi = 180 + self.tupCurrentCameraDir[0] 
        if fMX > self.fEdgeBound: 
            dx = cos(radians(old_Phi+180))*(fMX-self.fEdgeBound)/(1-self.fEdgeBound)*self.fPanRate/self.fZoomRate 
            dy = sin(radians(old_Phi+180))*(fMX-self.fEdgeBound)/(1-self.fEdgeBound)*self.fPanRate/self.fZoomRate 
            #print fMX, fMY, dx, dy 
          
        if fMX < -1*self.fEdgeBound: 
            dx = cos(radians(old_Phi+180))*(fMX+self.fEdgeBound)/(1-self.fEdgeBound)*self.fPanRate/self.fZoomRate 
            dy = sin(radians(old_Phi+180))*(fMX+self.fEdgeBound)/(1-self.fEdgeBound)*self.fPanRate/self.fZoomRate 
            #print fMX, fMY, dx ,dy 
          
        if fMY > self.fEdgeBound: 
            dx = -1*cos(radians(old_Phi+90))*(fMY-self.fEdgeBound)/(1-self.fEdgeBound)*self.fPanRate/self.fZoomRate 
            dy = -1*sin(radians(old_Phi+90))*(fMY-self.fEdgeBound)/(1-self.fEdgeBound)*self.fPanRate/self.fZoomRate 
            #print fMX, fMY, dx ,dy 
            
        if fMY < -1*self.fEdgeBound:        
            dx = -1*cos(radians(old_Phi+90))*(fMY+self.fEdgeBound)/(1-self.fEdgeBound)*self.fPanRate/self.fZoomRate 
            dy = -1*sin(radians(old_Phi+90))*(fMY+self.fEdgeBound)/(1-self.fEdgeBound)*self.fPanRate/self.fZoomRate 
            #print fMX, fMY, dx ,dy 
          
        if not self.booDebug: 
            self.tupCurrentCameraPos = (self.tupCurrentCameraPos[0] + dx, self.tupCurrentCameraPos[1] + dy, self.tupCurrentCameraPos[2]) 
            base.camera.setPos(self.tupCurrentCameraPos[0], self.tupCurrentCameraPos[1], self.tupCurrentCameraPos[2]) 
          
    def DoDragPan(self, fMX, fMY): 
        dx, dy = 0, 0 
        old_Phi = 180 + self.tupCurrentCameraDir[0] 
        dMX = fMX - self.fLastMouseX 
        dMY = fMY - self.fLastMouseY 
        x_p = dMX*self.fDragPanRate/self.fZoomRate 
        y_p = dMY*self.fDragPanRate/self.fZoomRate 
        c_ = cos(radians(old_Phi+180)) 
        s_ = sin(radians(old_Phi+180)) 
        dx = -1*(c_*x_p - s_*y_p) 
        dy = -1*(s_*x_p + c_*y_p) 
        if self.booDebug: 
            print dx, dy 
        if not self.booDebug: 
            self.tupCurrentCameraPos = (self.tupCurrentCameraPos[0] + dx, self.tupCurrentCameraPos[1] + dy, self.tupCurrentCameraPos[2]) 
            base.camera.setPos(self.tupCurrentCameraPos[0], self.tupCurrentCameraPos[1], self.tupCurrentCameraPos[2]) 
            self.fLastMouseX = fMX 
            self.fLastMouseY = fMY 
       
    def DoOrbit(self, fMX, fMY): 
        if not self.booDebug: 
            dMX = fMX - self.fLastMouseX 
            dMY = fMY - self.fLastMouseY 
        else: 
            dMX = fMX 
            dMY = fMY 
        dTheta = -1*dMY * self.fThetaRate 
        dPhi = -1*dMX * self.fPhiRate 
       
        old_Theta = -1*self.tupCurrentCameraDir[1] 
        old_Phi = 180 + self.tupCurrentCameraDir[0] 
        old_xyz_r = self.tupCurrentCameraPos[2]/sin(abs(radians(self.tupCurrentCameraDir[1]))) 
        old_xy_r = self.tupCurrentCameraPos[2]/tan(abs(radians(self.tupCurrentCameraDir[1]))) 
        old_x = -1*old_xy_r*cos(radians(self.tupCurrentCameraDir[0]+90)) 
        old_y = -1*old_xy_r*sin(radians(self.tupCurrentCameraDir[0]+90)) 

        if self.booDebug: 
            print "Old target 2 cam theta", old_Theta 
            print "Old Camera pos", self.tupCurrentCameraPos 
            print "Old Camera dir", self.tupCurrentCameraDir 
       
        new_Theta = old_Theta + dTheta 
        if new_Theta < self.tupThetaLimit[0]: 
            new_Theta = 5 
        if new_Theta > self.tupThetaLimit[1]: 
            new_Theta = 90 
        new_Phi = old_Phi + dPhi 

        nz = 1.*old_xyz_r*sin(radians(new_Theta)) 
        new_xy_r = 1.*old_xyz_r*cos(radians(new_Theta)) 
        new_x = new_xy_r*cos(radians(new_Phi+90)) 
        new_y = new_xy_r*sin(radians(new_Phi+90)) 
       
        self.tupCurrentCameraPos = (self.tupCurrentCameraPos[0] + new_x - old_x, self.tupCurrentCameraPos[1] + new_y - old_y, nz) 
        self.tupCurrentCameraDir = (new_Phi - 180, -1*new_Theta, 0) 

        if self.booDebug: 
            print "New target 2 cam theta", new_Theta 
            print "New Camera Pos", self.tupCurrentCameraPos 
            print "New Camera dir", self.tupCurrentCameraDir 
          
        if not self.booDebug: 
            base.camera.setPos(self.tupCurrentCameraPos[0], self.tupCurrentCameraPos[1], self.tupCurrentCameraPos[2]) 
            base.camera.setHpr(self.tupCurrentCameraDir[0], self.tupCurrentCameraDir[1], self.tupCurrentCameraDir[2]) 
            self.fLastMouseX = fMX 
            self.fLastMouseY = fMY 
       
    def GoHome(self): 
        base.camera.setPos(self.tupInitCameraPos[0], self.tupInitCameraPos[1], self.tupInitCameraPos[2]) 
        base.camera.setHpr(self.tupInitCameraDir[0], self.tupInitCameraDir[1], self.tupInitCameraDir[2]) 
        self.tupCurrentCameraPos = self.tupInitCameraPos 
        self.tupCurrentCameraDir = self.tupInitCameraDir 

    def StartDragPan(self): 
        self.booDragPanning = True 
        if base.mouseWatcherNode.hasMouse(): 
            mpos = base.mouseWatcherNode.getMouse() 
            self.fLastMouseX = mpos.getX() 
            self.fLastMouseY = mpos.getY() 

    def StopDragPan(self): 
        self.booDragPanning = False 
       
    def StartCameraOrbit(self): 
        self.booOrbiting = True 
        if base.mouseWatcherNode.hasMouse(): 
            mpos = base.mouseWatcherNode.getMouse() 
            self.fLastMouseX = mpos.getX() 
            self.fLastMouseY = mpos.getY() 

    def StopCameraOrbit(self): 
        self.booOrbiting = False 

    def ZoomCameraOut(self): 
        old_Theta = -1*self.tupCurrentCameraDir[1] 
        old_Phi = 180 + self.tupCurrentCameraDir[0] 
        old_xyz_r = self.tupCurrentCameraPos[2]/sin(abs(radians(self.tupCurrentCameraDir[1]))) 
        old_xy_r = self.tupCurrentCameraPos[2]/tan(abs(radians(self.tupCurrentCameraDir[1]))) 
        old_x = -1*old_xy_r*cos(radians(self.tupCurrentCameraDir[0]+90)) 
        old_y = -1*old_xy_r*sin(radians(self.tupCurrentCameraDir[0]+90)) 

        new_xyz_r = old_xyz_r*self.fZoomRate 
        nz = 1.*new_xyz_r*sin(radians(old_Theta)) 
        new_xy_r = 1.*new_xyz_r*cos(radians(old_Theta)) 
        new_x = new_xy_r*cos(radians(old_Phi+90)) 
        new_y = new_xy_r*sin(radians(old_Phi+90)) 
       
        self.tupCurrentCameraPos = (self.tupCurrentCameraPos[0] + new_x - old_x, self.tupCurrentCameraPos[1] + new_y - old_y, nz) 
        base.camera.setPos(self.tupCurrentCameraPos[0], self.tupCurrentCameraPos[1], self.tupCurrentCameraPos[2]) 

    def ZoomCameraIn(self): 
        old_Theta = -1*self.tupCurrentCameraDir[1] 
        old_Phi = 180 + self.tupCurrentCameraDir[0] 
        old_xyz_r = self.tupCurrentCameraPos[2]/sin(abs(radians(self.tupCurrentCameraDir[1]))) 
        old_xy_r = self.tupCurrentCameraPos[2]/tan(abs(radians(self.tupCurrentCameraDir[1]))) 
        old_x = -1*old_xy_r*cos(radians(self.tupCurrentCameraDir[0]+90)) 
        old_y = -1*old_xy_r*sin(radians(self.tupCurrentCameraDir[0]+90)) 

        new_xyz_r = old_xyz_r/self.fZoomRate 
        nz = 1.*new_xyz_r*sin(radians(old_Theta)) 
        new_xy_r = 1.*new_xyz_r*cos(radians(old_Theta)) 
        new_x = new_xy_r*cos(radians(old_Phi+90)) 
        new_y = new_xy_r*sin(radians(old_Phi+90)) 
         
        self.tupCurrentCameraPos = (self.tupCurrentCameraPos[0] + new_x - old_x, self.tupCurrentCameraPos[1] + new_y - old_y, nz) 
        base.camera.setPos(self.tupCurrentCameraPos[0], self.tupCurrentCameraPos[1], self.tupCurrentCameraPos[2]) 


class clPickerTool(DirectObject.DirectObject):
    def __init__(self): 
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0))
        traverser = CollisionTraverser()
        self.tr = traverser
        collisionhandler = CollisionHandlerQueue()
        self.cHandQ = collisionhandler
        pickerNode = CollisionNode('mouseRay')
        pickerNP = base.camera.attachNewNode(pickerNode)
        pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        pickerRay = CollisionRay()
        self.pr = pickerRay
        pickerNode.addSolid(pickerRay)
        self.tr.addCollider(pickerNP, self.cHandQ)
      
        cm = CardMaker('tile') 
        cm.setFrame(0, base.tile_size, 0, base.tile_size) 
        self.select_tile = render.attachNewNode(cm.generate())
        self.select_tile.setPos(0, 0, 0)
        self.select_tile.setColor(1, 0, 0)
        self.select_tile.lookAt(0, 0, -1)
        
        cmMT = CardMaker('movetile')
        cmMT.setFrame(0, base.tile_size, 0, base.tile_size) 
        self.move_tile = render.attachNewNode(cmMT.generate())
        self.move_tile.setPos(0, 0, 0)
        self.move_tile.lookAt(0, 0, -1)        
        self.move_tile.hide()
        
        self.mouse_tile = Point3()
        self.last_mouse_tile = None
      
        self.accept('mouse1', self.PickObject)
        taskMgr.add(self.GetMousePos,'GetMousePosTask')    
    
    def hide_move_tile(self):
        self.move_tile.setPos(0, 0, -50)
        self.move_tile.hide()
    
    def GetMousePos(self, task): 
        if base.mouseWatcherNode.hasMouse(): 
            mpos = base.mouseWatcherNode.getMouse() 
            pos3d = Point3() 
            nearPoint = Point3() 
            farPoint = Point3() 
            base.camLens.extrude(mpos, nearPoint, farPoint) 
            if self.plane.intersectsLine(pos3d, render.getRelativePoint(camera, nearPoint), render.getRelativePoint(camera, farPoint)): 
                x = pos3d.getX()
                y = pos3d.getY()
                if x >= 0 and x < base.level.x and y >= 0 and y < base.level.y:
                    self.mouse_tile = Point3(int(x), int(y), 0)
                else:
                    self.mouse_tile = None
            if base.game_state['movement'] == 1 and base.picked_unit != None and self.mouse_tile != None:
                if self.mouse_tile != self.last_mouse_tile:
                    self.last_mouse_tile = self.mouse_tile
                    for i in base.picked_unit.closed_tile_list:
                        if self.mouse_tile.x == i[0].x and self.mouse_tile.y == i[0].y:
                            if base.picked_unit.current_AP - i[2] >= 2:
                                self.move_tile.setColor(0, 1, 0)
                            else:
                                self.move_tile.setColor(0, 0, 1)
                            self.move_tile.setPos(self.mouse_tile)
                            self.move_tile.show()
                            break
                        else:
                            self.move_tile.hide()
            #print base.gameState['movement'], base.pickedUnit
        return task.again 
      
    def PickObject(self):
        if base.mouseWatcherNode.hasMouse():
            if base.game_state['movement'] == 0:
                old_picked_unit = base.picked_unit
                pickedObj = None
                base.picked_unit = None
                mpos = base.mouseWatcherNode.getMouse()
                self.pr.setFromLens(base.camNode, mpos.getX(), mpos.getY())
                self.tr.traverse(render)
                if self.cHandQ.getNumEntries() > 0:
                    # This is so we get the closest object.
                    self.cHandQ.sortEntries()
                    pickedObj = self.cHandQ.getEntry(0).getIntoNodePath()
                    if pickedObj.findNetTag('Unit').getTag('Unit') == 'true' and base.game_state['movement'] == 0:
                        base.picked_unit = base.units[pickedObj.findNetTag('Name').getTag('Name')]
                        pos = base.calc_world_pos(base.picked_unit.model.getPos())
                        self.select_tile.setPos(pos)
                
                if pickedObj == None and self.mouse_tile != None:
                    x = floor(self.mouse_tile.x)
                    y = floor(self.mouse_tile.y)
                    if x >= base.level.x * -base.tile_size and x < base.level.x * base.tile_size and y >= base.level.y * -base.tile_size and y < base.level.y * base.tile_size:
                        self.select_tile.setPos(floor(self.mouse_tile.x), floor(self.mouse_tile.y), 0)
                        for u in base.units.itervalues():
                            base.picked_unit = None
                            if base.calc_world_pos(u.model.getPos()) == self.select_tile.getPos():
                                base.picked_unit = u
                                break 
                
                if base.picked_unit != None and base.picked_unit != old_picked_unit:
                    base.picked_unit.model.play('selected')
                    base.picked_unit.talk('select')
            else:
                dest = Point2(self.mouse_tile.x, self.mouse_tile.y)
                base.picked_unit.move(dest)
                base.toggle_state('movement')
