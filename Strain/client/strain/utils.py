#############################################################################
# IMPORTS
#############################################################################

# python imports
import string

# panda3D imports
from panda3d.core import GeomNode, NodePath, TextureStage, Vec4, Point2, Point3
from direct.actor.Actor import Actor

# strain related imports


#############################################################################
# GLOBALS
#############################################################################

CONSOLE_SYSTEM_ERROR = 1
CONSOLE_SYSTEM_MESSAGE = 2
CONSOLE_PLAYER1_TEXT = 3
CONSOLE_PLAYER2_TEXT = 4

GUI_BOTTOM_OFFSET = 0.3
GUI_TOP_OFFSET = 0.07
GUI_FONT = "verdana.ttf"
GUI_FONT_BOLD = "verdanab.ttf"

CONSOLE_SYSTEM_ERROR_TEXT_COLOR = (1, 0, 0, 1)
CONSOLE_SYSTEM_MESSAGE_TEXT_COLOR = (1, 1, 1, 1)
CONSOLE_PLAYER1_TEXT_COLOR = (0, 1, 0, 1)
CONSOLE_PLAYER2_TEXT_COLOR = (0, 0.8, 0, 1)

HEADING_NONE      = 0
HEADING_NW        = 1
HEADING_N         = 2
HEADING_NE        = 3
HEADING_W         = 4
HEADING_E         = 5
HEADING_SW        = 6
HEADING_S         = 7
HEADING_SE        = 8

TILE_SIZE = 2
GROUND_LEVEL = 0.0
MODEL_OFFSET = TILE_SIZE/2
UNIT_SCALE = 0.8
BULLET_SPEED = 15

marine_anim_dict = {}
marine_anim_dict['crouch'] = 'marine-crouch'
marine_anim_dict['die'] = 'marine-die'
marine_anim_dict['get_hit'] = 'marine-gethit'
marine_anim_dict['idle'] = 'marine-idle'
marine_anim_dict['idle_lowergun'] = 'marine-idlelowergun'
marine_anim_dict['jet_hover'] = 'marine-jethover'   
marine_anim_dict['jet_jump'] = 'marine-jetjump' 
marine_anim_dict['melee'] = 'marine-melee'
marine_anim_dict['overwatch'] = 'marine-overwatch'
marine_anim_dict['run'] = 'marine-run'
marine_anim_dict['setup'] = 'marine-setup'
marine_anim_dict['shoot'] = 'marine-shoot'
marine_anim_dict['shoot_add'] = 'marine-shootadditive'
marine_anim_dict['stand_up'] = 'marine-standup'
marine_anim_dict['taunt'] = 'marine-taunt'
marine_anim_dict['use'] = 'marine-use'
marine_anim_dict['walk'] = 'marine-walk'

anim_dict = {}
anim_dict['marine'] = marine_anim_dict

marine_unit_types = {}
marine_unit_types['standard'] = 'marine_standard'
marine_unit_types['heavy'] = 'marine_heavy'
marine_unit_types['jumper'] = 'marine_jumper'
marine_unit_types['scout'] = 'marine_scout'
marine_unit_types['medic'] = 'marine_medic'
marine_unit_types['sergeant'] = 'marine_sergeant'

unit_type_dict = {}
unit_type_dict['marine'] = marine_unit_types

#############################################################################
# METHODS
#############################################################################

#===============================================================================
# flattenReallyStrong
# source by Craig from Panda3d forums
# http://www.panda3d.org/forums/viewtopic.php?t=12096
#===============================================================================
def flattenReallyStrong(n):
    """
    force the passed nodepath into a single geomNode, then flattens the
    geomNode to minimize geomCount.
    
    In many cases, flattenStrong is not enough, and for good reason.
    This code ignores all potential issues and forces it into one node.
    It will alwayse do so.
    
    RenderStates are preserved, transformes are applied, but tags,
    special node classes and any other such data is all lost.
    
    This modifies the passed NodePath as a side effect and returns the
    new NodePath.
    """
    # make sure all the transforms are applied to the geoms
    n.flattenLight()
    # make GeomNode to store results in.
    g=GeomNode("flat_"+n.getName())
    g.setState(n.getState())
    
    # a little helper to process GeomNodes since we need it in 2 places
    def f(c):
        rs=c.getState(n)
        gg=c.node()
        for i in xrange(gg.getNumGeoms()):
            g.addGeom(gg.modifyGeom(i),rs.compose(gg.getGeomState(i)))
    
    # special case this node being a GeomNode so we don't skips its geoms.
    if n.node().isGeomNode(): f(n)
    # proccess all GeomNodes
    for c in n.findAllMatches('**/+GeomNode'): f(c)
       
    nn=NodePath(g)
    nn.setMat(n.getMat())
    # merge geoms
    nn.flattenStrong()
    return nn
  
def normalize(myVec):
    myVec.normalize()  
    return myVec

def clampToHeading(h):
    key = HEADING_NONE
    if h >= -22.5 and h < 22.5:
        key = HEADING_N
    elif h >= 22.5 and h < 67.5:
        key = HEADING_NW
    elif h >= 67.5 and h < 112.5:
        key = HEADING_W
    elif h >= 112.5 and h < 157.5:
        key = HEADING_SW
    elif (h >= 157.5 and h <= 180) or (h >= -180 and h < -157.5):
        key = HEADING_S
    elif h >= -157.5 and h < -112.5:
        key = HEADING_SE
    elif h >= -112.5 and h < -67.5:
        key = HEADING_E
    elif h >= -67.5 and h < -22.5:
        key = HEADING_NE
    return key

def getHeadingAngle(h):
    if h == HEADING_N:
        angle = 0
    elif h == HEADING_NW:
        angle = 45
    elif h == HEADING_W:
        angle = 90
    elif h == HEADING_SW:
        angle = 135
    elif h == HEADING_S:
        angle = 180
    elif h == HEADING_SE:
        angle = -135
    elif h == HEADING_E:
        angle = -90
    elif h == HEADING_NE:
        angle = -45
    else:
        angle = 0
    return angle

def getHeadingTile(h, dest):
    int_h = int(h)
    if int_h == HEADING_N:
        offset = (0, 1)
    elif int_h == HEADING_NW:
        offset = (-1, 1)
    elif int_h == HEADING_W:
        offset = (-1, 0)
    elif int_h == HEADING_SW:
        offset = (-1, -1)
    elif int_h == HEADING_S:
        offset = (0, -1)
    elif int_h == HEADING_SE:
        offset = (1, -1)
    elif int_h == HEADING_E:
        offset = (1, 0)
    elif int_h == HEADING_NE:
        offset = (1, 1)
    else:
        offset = (0, 0)
    return tuple([item1 + item2 for item1, item2 in zip(dest, offset)])


def getUnitWeapons(unit):
    wpn_list = [unit['ranged_weapon']['name'], unit['melee_weapon']['name']]
    return wpn_list

def loadUnit(race, type, team, wpn1=None, wpn2=None):
    model = Actor(unit_type_dict[race][type])
    model.loadAnims(anim_dict[race])
    if team == '1':
        tex = loader.loadTexture(unit_type_dict[race][type] + ".png")
    elif team == '2':
        tex = loader.loadTexture(unit_type_dict[race][type] + "2.png")
    model.setTexture(tex)
    if wpn1 != None:
        rnp = model.exposeJoint(None,"modelRoot","Wrist.R")
        if wpn1 == 'Defaulter':
            rwp = loader.loadModel('gun1')
            rwp.setTexture(loader.loadTexture('gun.png'))
            rwp.reparentTo(rnp)
        elif wpn1 == 'Heavy Defaulter':
            rwp = loader.loadModel('gun1')
            rwp.setTexture(loader.loadTexture('gun.png'))
            rwp.reparentTo(rnp)
        elif wpn1 == 'Default Pistol':
            rwp = loader.loadModel('gun1')
            rwp.setTexture(loader.loadTexture('gun_green.png'))
            rwp.reparentTo(rnp)
        elif wpn1 == 'Plasma Pistol':
            rwp = loader.loadModel('gun1')
            rwp.setTexture(loader.loadTexture('gun_orange.png'))
            rwp.reparentTo(rnp)
    return model 

#===============================================================================
# nodeCoordIn2d
# source by birukoff from Panda3d forums
# http://www.panda3d.org/forums/viewtopic.php?p=22023
#===============================================================================
def nodeCoordIn2d(nodePath):
    coord3d = nodePath.getPos(base.cam)
    coord2d = Point2()
    base.camLens.project(coord3d, coord2d)
    coordInRender2d = Point3(coord2d[0], 0, coord2d[1])
    coordInAspect2d = aspect2d.getRelativePoint(render2d, coordInRender2d)
    return coordInAspect2d

def pointCoordIn2d(point):
    coord3d = base.cam.getRelativePoint(render, point) 
    coord2d = Point2()
    base.camLens.project(coord3d, coord2d)
    coordInRender2d = Point3(coord2d[0], 0, coord2d[1])
    coordInAspect2d = aspect2d.getRelativePoint(render2d, coordInRender2d)
    return coordInAspect2d
