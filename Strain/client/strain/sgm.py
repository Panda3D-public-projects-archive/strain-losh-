#############################################################################
# IMPORTS
#############################################################################

# python imports

# panda3D imports
from panda3d.core import TextNode, NodePath, VBase4, CardMaker, Vec4, Vec3#@UnresolvedImport
from panda3d.core import ShadeModelAttrib, DirectionalLight, AmbientLight, PointLight#@UnresolvedImport
from panda3d.core import CullBinManager, CullBinEnums#@UnresolvedImport
from panda3d.core import TransparencyAttrib, AntialiasAttrib, Shader#@UnresolvedImport
from panda3d.core import SceneGraphAnalyzerMeter#@UnresolvedImport


# strain related imports
from strain.voxelgen import VoxelGenerator
from strain.unitmodel import UnitModel
import strain.utils as utils
from strain.share import *

#========================================================================
#
class SceneGraph():
    def __init__(self, parent):
        self.parent = parent
        
        # Main node in a scene graph. Everything should be reparented to this node or another node under this node
        # This node is reparented to render
        self.node = render.attachNewNode("master")
        
        # Set up flag dictionary
        self.comp_inited = {}
        self.comp_inited['level'] = False
        self.comp_inited['lights'] = False
        self.comp_inited['units'] = False
        self.comp_inited['alt_render'] = False
        
        # Set up dictionary for unit nodepaths
        self.unit_np_dict = {}
        
        self.off_model = None
        
        self.turn_np = NodePath("turn_arrows_np")
        self.turn_np.reparentTo(render)
        self.dummy_turn_pos_node = NodePath("dummy_turn_pos_node")
        self.dummy_turn_dest_node = NodePath("dummy_turn_dest_node")        
        self.unit_move_destination = None
        self.unit_move_orientation = utils.HEADING_NONE
        self.move_timer = 0
        self.movetext_np = None
        self.enemyunittiles_np = None
        
        self.tile_cards = []
        self.tile_cards_np = render.attachNewNode('tile_cards_np')
        self.tile_cards_np.setLightOff()
        
        self.initOutlineShader()
        
        #meter = SceneGraphAnalyzerMeter('meter', render.node())
        #meter.setupWindow(base.win)      
        
        bins = CullBinManager.getGlobalPtr()
        bins.addBin('highlight', CullBinEnums.BTStateSorted, 25)
        
        #print "base.win.getGsg().getMaxTextureStages() = "+str(base.win.getGsg().getMaxTextureStages())
    
    def loadLevel(self, level):
        if self.comp_inited['level']:
            return
        
        self.level_node = self.node.attachNewNode("level_node")        
        self.level_mesh = VoxelGenerator(self, level)
        self.level_mesh.createLevel()
        self.comp_inited['level'] = True
        
        #grid_tex = loader.loadTexture('grid2.png')
        #grid_tex.setMagfilter(Texture.FTLinearMipmapLinear)
        #grid_tex.setMinfilter(Texture.FTLinearMipmapLinear)
        for i in xrange(0, level.maxX):
            l = []
            for j in xrange(0, level.maxY):
                cm = CardMaker('cm') 
                cpos = self.tile_cards_np.attachNewNode(cm.generate()) 
                cpos.setP(render, -90)
                cpos.setPos(render, i, j, utils.GROUND_LEVEL)
                cpos.setDepthOffset(1)
                #cpos.setTexture(grid_tex)
                #cpos.node().setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd))
                cpos.setTransparency(TransparencyAttrib.MAlpha)
                cpos.setBin('highlight', 25)
                cpos.setCollideMask(0)
                cpos.detachNode()
                l.append(cpos)
            self.tile_cards.append(l)
            
        for i in xrange(0, level.maxX):
            t = TextNode('node name')
            t.setText( "%s" % i)
            tnp = self.level_node.attachNewNode(t)
            tnp.setColor(1, 1, 1)
            tnp.setScale(0.5, 0.5, 0.5)
            tnp.setPos(i+0.3, -0.3, 0.5)
            tnp.setBillboardPointEye()
            tnp.setLightOff()
        for i in xrange(0, level.maxY):
            t = TextNode('node name')
            t.setText( "%s" % i)
            tnp = self.level_node.attachNewNode(t)
            tnp.setColor(1, 1, 1)
            tnp.setScale(0.5, 0.5, 0.5)
            tnp.setPos(-0.3, i+0.3, 0.5)
            tnp.setBillboardPointEye()
            tnp.setLightOff()
        
    def deleteLevel(self):
        if self.comp_inited['level'] == False:
            return
        
        self.level_node.removeNode()
        self.comp_inited['level'] = False
    
    def initLights(self):
        if self.comp_inited['lights']:
            return
        
        shade = ShadeModelAttrib.make(ShadeModelAttrib.MSmooth)
        render.setAttrib(shade)
        dlight1 = DirectionalLight("dlight1")
        dlight1.setColor(VBase4(0.5, 0.5, 0.5, 1.0))
        #dlight1.setShadowCaster(True, 512, 512)
        dlnp1 = render.attachNewNode(dlight1)
        dlnp1.setHpr(0, -60, 0)
        render.setLight(dlnp1)
        """
        plight = PointLight('plight')
        plight.setColor(VBase4(0.5, 0.5, 0.5, 1.2))
        plnp = render.attachNewNode(plight)
        plnp.setPos(5, 5, 1.5)
        render.setLight(plnp)
        a = loader.loadModel("camera")
        a.reparentTo(plnp)
        a.setScale(0.4, 0.4, 0.4)
        """
        alight = AmbientLight("alight")
        alight.setColor(VBase4(0.4, 0.4, 0.4, 1.0))
        alnp = render.attachNewNode(alight)
        render.setLight(alnp) 
        self.comp_inited['lights'] = True
    
    def loadUnits(self):
        if self.comp_inited['units']:
            return
        
        self.unit_node = self.node.attachNewNode('unit_node')
                    
        for unit_id in self.parent.units.iterkeys():
            wpn_list = utils.getUnitWeapons(self.parent.units[unit_id])
            unit_model = self.loadUnit(unit_id, wpn_list)
            self.showUnit(unit_model)
                        
        self.comp_inited['units'] = True  
        
    def loadUnit(self, unit_id, wpn_list):
        um = UnitModel(self, unit_id)
        # Keep unit nodepath in dictionary of all unit nodepaths
        self.unit_np_dict[unit_id] = um
        return um
    
    def showUnit(self, unit_model, pos=None, heading=None):
        if pos:
            unit_model.node.setPos(pos)
        if heading:
            unit_model.node.setH(heading)
        unit_model.node.reparentTo(self.unit_node)
       
    def hideUnit(self, unit_id):
        unit_model = self.unit_np_dict[unit_id] 
        self.unit_np_dict.pop(unit_id)
        unit_model.node.remove()
        del unit_model
        
    def detachUnit(self, unit_id):
        unit_model = self.unit_np_dict[unit_id] 
        unit_model.node.detachNode()
    
    def deleteUnits(self):
        if self.comp_inited['units'] == False:
            return
        
        self.unit_node.removeNode()
        self.unit_np_dict = {}
        self.comp_inited['units'] = False
          
    
    def initAltRender(self):
        """Initializes off screen buffer used to render models and animations for unit portraits."""
        if self.comp_inited['alt_render']:
            return
        
        self.alt_buffer = base.win.makeTextureBuffer("texbuf", 256, 256)
        self.alt_render = NodePath("offrender")
        self.alt_cam = base.makeCamera(self.alt_buffer)
        self.alt_cam.reparentTo(self.alt_render)        
        self.alt_cam.setPos(0,0,0)
        #lens = PerspectiveLens()#OrthographicLens()
        #lens.setFilmSize(20*.5, 15*.5) # or whatever is appropriate for your scene
        #self.alt_cam.node().setLens(lens)
        #base.cam.node().getLens().setNear(0.1)
        #base.cam.node().getLens().setFar(32*1.5)
        #lens.setFov(20)
        self.alt_render.setLightOff()
        self.alt_render.setFogOff() 
        self.parent.interface.unit_card.setTexture(self.alt_buffer.getTexture())  
        self.comp_inited['alt_render'] = True
    
    def clearAltRenderModel(self):
        if not self.comp_inited['alt_render']:
            return
        
        if self.off_model:
            self.off_model.cleanup()
            self.off_model.remove()
        
        
    def loadAltRenderModel(self, unit_id):
        if not self.comp_inited['alt_render']:
            return
        wpn_list = utils.getUnitWeapons(self.parent.units[unit_id])
        self.off_model = UnitModel(self, unit_id, off=True)
        self.off_model.model.reparentTo(self.alt_render)
        
    def showUnitAvailMove(self, unit_id):
        """Displays visual indicator of tiles which are in movement range of the selected unit."""
        self.hideUnitAvailMove()
        unit = self.parent.units[unit_id]
        if self.parent.turn_player != self.parent.player:
            return
        if unit:
            unit['move_dict'] = getMoveDict(unit, self.parent.level, self.parent.units)
            self.parent.units[unit_id]['move_dict'] = unit['move_dict']
            move_dict = unit['move_dict']
            self.movetext_np = NodePath("movetext_np")
            self.movetext_np.setLightOff()
            for tile in move_dict:
                text = TextNode('node name')
                text.setText( "%s" % move_dict[tile])
                text.setAlign(TextNode.ACenter)
                textNodePath = self.movetext_np.attachNewNode(text)
                textNodePath.setPos(render, tile[0]+0.45, tile[1]+0.45, utils.GROUND_LEVEL+0.04)
                textNodePath.setColor(1, 1, 1)
                textNodePath.setScale(0.4, 0.4, 0.4)
                textNodePath.setBillboardPointEye()
                self.tile_cards[tile[0]][tile[1]].setColor(utils.WALKABLE_TILE_COLOR)
                self.tile_cards[tile[0]][tile[1]].reparentTo(self.tile_cards_np)                  
            self.movetext_np.reparentTo(self.node)  

    def hideUnitAvailMove(self):
        if self.movetext_np:
            self.movetext_np.removeNode() 
            for c in self.tile_cards_np.getChildren():
                c.detachNode()
    
    def showVisibleEnemies(self, unit_id):
        self.hideVisibleEnemies()
        unit = self.parent.units[unit_id]     
        for u in self.parent.units.itervalues():
            if self.parent.isThisEnemyUnit(u['id']):
                if getLOSOnLevel(unit, u, self.parent.level) > 0:
                    unit_model = self.parent.sgm.unit_np_dict[u['id']]
                    unit_model.setEnemyVisible()
        
    def hideVisibleEnemies(self):
        for u in self.parent.units.itervalues():
            if self.parent.isThisEnemyUnit(u['id']):
                self.parent.sgm.unit_np_dict[u['id']].clearEnemyVisible()   
            
    def setBullet(self, b):
        b.reparentTo(render)
    
    def deleteBullet(self, b):
        b.removeNode()
        
    def setDamageNode(self, d, u):
        d.reparentTo(u)
        
    def deleteDamageNode(self, d):
        d.removeNode()  
        
    def playUnitStateAnim(self, unit_id):
        # Check if we have toggled overwatch
        unit = self.parent.units[unit_id]
        unit_model = self.unit_np_dict[unit_id]
        if unit_model.isOverwatch == False and unit['overwatch'] == True:
            unit_model.isOverwatch = True
            unit_model.pauseAllAnims()
            unit_model.overwatch_anim.start()
        elif unit_model.isOverwatch == True and unit['overwatch'] == False:
            unit_model.isOverwatch = False
            unit_model.pauseAllAnims()
            unit_model.standup_anim.start()
        elif unit_model.isSetup == False:
            try:
                if unit['set_up'] == True:
                    unit_model.isSetup = True
                    unit_model.pauseAllAnims()
                    unit_model.setup_anim.start()
            except:
                None
        elif unit_model.isSetup == True:
            try:
                if unit['set_up'] == False:
                    unit_model.isSetup = False
                    unit_model.pauseAllAnims()
                    unit_model.standup_anim.start()
            except:
                None
    def deleteTurnNode(self, d):
        d.removeNode()

    def initOutlineShader(self):  
        self.light_dummy = NodePath("outline_light_dummy_node")      
        self.light_input = NodePath("outline_light_input_node")
        self.light_input.reparentTo(self.light_dummy) 
        self.light_input.setPos(5, 0, 1) 
        self.light_dummy.setShaderOff() 
        self.light_dummy.hprInterval(1,Vec3(360,0,0)).loop() 
        self.SHA_outline = Shader.load('./data/shaders/facingRatio1.sha') 

    def setOutlineShader(self, np, color=Vec4(1, 1, 1, 0), power=1.1):
        facingRatioPower = power
        envirLightColor = color    

        self.light_dummy.reparentTo(np)
        self.light_dummy.setPos(np, 0, 0, 1)
        
        np.setShader(self.SHA_outline) 
        np.setShaderInput('cam', base.camera) 
        np.setShaderInput('light', self.light_input) 
        np.setShaderInput('envirLightColor', envirLightColor * facingRatioPower) 
        np.setAntialias(AntialiasAttrib.MMultisample) 
        
    def clearOutlineShader(self, np):
        self.light_dummy.detachNode()
        np.setShaderOff()