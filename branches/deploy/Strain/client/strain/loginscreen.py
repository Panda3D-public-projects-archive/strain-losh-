#############################################################################
# IMPORTS
#############################################################################

# python imports


# panda3D imports
from panda3d.core import TextNode, BitMask32, TextureStage, NodePath, DirectionalLight, AmbientLight, Vec4, Vec3, VBase4#@UnresolvedImport
from direct.gui.DirectGui import DirectButton, DirectEntry, DirectLabel#@UnresolvedImport
from direct.gui.OnscreenText import OnscreenText#@UnresolvedImport
from direct.gui.OnscreenImage import OnscreenImage
from direct.filter.CommonFilters import CommonFilters#@UnresolvedImport

# strain related imports
import strain.utils as utils


class LoginScreen():
    def __init__(self, parent):
        self.parent = parent
        font = loader.loadFont('frizqt__.ttf')
        legofont = loader.loadFont('legothick.ttf')
        self.label_username = DirectLabel(text = "Username:", scale=.05, frameColor=(0,0,0,0), text_font=font, text_align=TextNode.ARight, text_fg=(1,1,1,1))
        self.label_password = DirectLabel(text = "Password:", scale=.05, frameColor=(0,0,0,0), text_font=font, text_align=TextNode.ARight, text_fg=(1,1,1,1))
        self.button = DirectButton(text = ("Login"),scale=.05,command=self.loginButPressed, text_font=font, text_align=TextNode.ACenter)
        self.entry_username = DirectEntry(scale=.05,initialText="", numLines = 1,focus=1,command=self.loginButPressed, text_font=font)
        self.entry_password = DirectEntry(scale=.05,initialText="", numLines = 1,command=self.loginButPressed, text_font=font)
        self.label_username.reparentTo(aspect2d)
        self.label_username.setPos(-0.2, 0, -0.4)
        self.label_password.reparentTo(aspect2d)
        self.label_password.setPos(-0.2, 0, -0.5)        
        self.entry_username.reparentTo(aspect2d)
        self.entry_username.setPos(-0.1, 0, -0.4)    
        self.entry_password.reparentTo(aspect2d)
        self.entry_password.setPos(-0.1, 0, -0.5)
        self.button.reparentTo(aspect2d)
        self.button.setPos(0, 0, -0.6) 
        
        self.button_red = DirectButton(text = ("Login as RED"),scale=.05,command=self.loginButRedPressed,text_font=font, text_align=TextNode.ACenter)
        self.button_red.reparentTo(aspect2d)
        self.button_red.setPos(0.5, 0, -0.6) 
        
        self.button_blue = DirectButton(text = ("Login as BLUE"),scale=.05,command=self.loginButBluePressed, text_font=font, text_align=TextNode.ACenter)
        self.button_blue.reparentTo(aspect2d)
        self.button_blue.setPos(0.5, 0, -0.7)         
        
        self.textObject = OnscreenText(text = 'STRAIN', pos = (0, 0.4), scale = 0.2, font=legofont, fg = (1,0,0,1))
    
        self.setScene()
    
    def cleanup(self):
        self.label_username.remove()
        self.label_password.remove()
        self.entry_username.remove()          
        self.entry_password.remove()        
        self.parent.login.button.remove()
        self.parent.login.button_red.remove()
        self.parent.login.button_blue.remove()
        self.parent.login.textObject.remove()
        self.unit1.cleanup()
        self.unit1.remove()
        self.unit2.cleanup()
        self.unit2.remove()
        self.unit3.cleanup()
        self.unit3.remove()
        self.unit4.cleanup()
        self.unit4.remove()
        self.plane.remove()
        self.shadowCameraRotNode.remove()
        self.initial.remove()
        render.clearLight(self.ambientLight)
        render.clearLight(self.sun)
        self.ambientLight.remove()
        self.sun.remove()
        
        render.setShaderOff()
         
        self.parent = None
    
    def loginButPressed(self, text=None):
        # TODO: ogs: loginButPressed bi trebao inicijalizirati net konekciju prema login serveru
        self.parent.player = self.entry_username.get()
        if self.parent.player != "Blue" and self.parent.player != "Red":
            self.parent.player = "Red"

    def loginButRedPressed(self, text=None):
        self.parent.player = "Red"
        # TODO: ogs: Inace cu znati player_id kad se ulogiram
        self.parent.player_id = '1'
        self.parent.fsm.request('Browser')
        
    def loginButBluePressed(self, text=None):
        self.parent.player = "Blue"
        # TODO: ogs: Inace cu znati player_id kad se ulogiram
        self.parent.player_id = '2'
        self.parent.fsm.request('Browser')

    def setScene(self):
        # Set up the camera
        #base.cam.setPos(0, -15, 15)
        #base.cam.lookAt(0, 0, 0)
        
        # Load the background
        self.plane = loader.loadModel("plane")
        self.plane.reparentTo(render)
        self.plane.setScale(20)
        self.plane.setColor(0.2, 0.3, 0.3)
        self.plane.setPosHpr(0, 0, 0, 0, -90, 0)

        # The ground does not need to be sceen by the shadow camera:
        self.plane.hide(BitMask32.bit(1))

        # We use a blend stage to apply the texture:
        self.shadowStage = TextureStage("Shadow Stage")
        self.shadowStage.setMode(TextureStage.MBlend)

        # Create a buffer for storing the shadow texture,
        # the higher the buffer size the better quality the shadow.
        self.shadowBuffer = base.win.makeTextureBuffer("Shadow Buffer",256,256)
        self.shadowBuffer.setClearColorActive(True)
        self.shadowBuffer.setClearColor((0,0,0,1))

        self.shadowCameraRotNode = render.attachNewNode('scn')
        self.shadowCameraRotNode.setPos(0, 0, 0)
        self.shadowCamera = base.makeCamera(self.shadowBuffer)
        self.shadowCamera.reparentTo(self.shadowCameraRotNode)

        self.lens = base.camLens
        self.lens.setAspectRatio(1/1)
        self.shadowCamera.node().setLens(self.lens)
        self.shadowCamera.node().setCameraMask(BitMask32.bit(1))

        # Make everything rendered by the shadow camera grey:
        self.initial = NodePath('initial')
        self.initial.setColor(.75,.75,.75,1,1)
        self.initial.setTextureOff(2)
        self.initial.setMaterialOff(2)
        self.initial.setLightOff(2)
        self.shadowCamera.node().setInitialState(self.initial.getState())

        # The cameras pos effects the shadows dirrection:
        self.shadowCamera.setPos(15,-15,20)
        self.shadowCamera.lookAt(0,0,0)
        self.shadowCameraRotNode.hprInterval(20,Vec3(360,0,0)).loop()

        # Make the shadows soft by bluring the screen:

        #self.filters = CommonFilters(self.shadowBuffer,self.shadowCamera)
        #self.filters.setBlurSharpen(0.0)

        self.shadowTexture = self.shadowBuffer.getTexture()

        # Draw the shadowTexture on sceen:
        #self.imageObject = OnscreenImage(image = self.shadowTexture,pos = (-.75,0,.75),scale=.2)

        # Project the shadow texture on to the plane:
        self.plane.projectTexture(self.shadowStage,self.shadowTexture,self.shadowCamera)
        
        # Models
        self.unit1 = utils.loadUnit('marine', 'sergeant', '1', 'Defaulter')
        self.unit1.reparentTo(render)
        self.unit1.setPosHpr(-5, 3, 0, 90, 0, 0)
        #self.unit1.loop('shoot')
        
        self.unit2 = utils.loadUnit('marine', 'medic', '1', 'Defaulter')
        self.unit2.reparentTo(render)
        self.unit2.setPosHpr(-3, 4, 0, 90, 0, 0)
        self.unit2.setPlayRate(1.5,'walk')
        #self.unit2.loop('walk')
        
        self.unit3 = utils.loadUnit('marine', 'heavy', '2', 'Heavy Defaulter')
        self.unit3.reparentTo(render)
        self.unit3.setPosHpr(6, 4, 0, -90, 0, 0)
        self.unit3.setPlayRate(1.5,'shoot')
        #self.unit3.loop('shoot') 
        
        self.unit4 = utils.loadUnit('marine', 'jumper', '2', 'Default Pistol')       
        self.unit4.reparentTo(render)
        self.unit4.setPosHpr(4.5, 3, 0, -90, 0, 0)
        #self.unit4.loop('jet_hover') 
        
        # Lighting:
        sun = DirectionalLight('Sun')
        sun.setColor(Vec4(.7,.7,.7,1))
        self.sun = render.attachNewNode(sun)
        self.sun.setHpr(45,-45,0)
        render.setLight(self.sun)
        ambientLight = AmbientLight('AmbientLight')
        ambientLight.setColor(VBase4(.5,.5,.5,1))
        self.ambientLight = render.attachNewNode(ambientLight)
        render.setLight(self.ambientLight)
        
        #base.disableMouse()
        render.setShaderAuto()
        