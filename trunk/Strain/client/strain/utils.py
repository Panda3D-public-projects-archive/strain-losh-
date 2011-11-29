#############################################################################
# IMPORTS
#############################################################################

# python imports

# panda3D imports
from pandac.PandaModules import GeomNode, NodePath
from direct.actor.Actor import Actor

# strain related imports


#############################################################################
# GLOBALS
#############################################################################

CONSOLE_SYSTEM_ERROR = 1
CONSOLE_SYSTEM_MESSAGE = 2
CONSOLE_PLAYER1_TEXT = 3
CONSOLE_PLAYER2_TEXT = 4

CONSOLE_SYSTEM_ERROR_TEXT_COLOR = (255, 0, 0, 1)
CONSOLE_SYSTEM_MESSAGE_TEXT_COLOR = (255, 255, 255, 1)
CONSOLE_PLAYER1_TEXT_COLOR = (0, 150, 0, 0.8)
CONSOLE_PLAYER2_TEXT_COLOR = (0, 100, 0, 0.8)

HEADING_NONE      = 0
HEADING_NW        = 1
HEADING_N         = 2
HEADING_NE        = 3
HEADING_W         = 4
HEADING_E         = 5
HEADING_SW        = 6
HEADING_S         = 7
HEADING_SE        = 8

GROUND_LEVEL = 0.3

armour_dict = {}
armour_dict['power_armour_common'] = ["power_armour_common"]
armour_dict['power_armour_rare'] = ["power_armour_rare"]
armour_dict['power_armour_epic'] = ["power_armour_epic"]
armour_dict['power_armour_commander'] = ["power_armour_commander"]

head_dict = {}
head_dict['space_marine_head'] = ["space_marine_head"]
head_dict['assault_marine_head'] = ["assault_marine_head"]        
head_dict['gabriel_head'] = ["gabriel_head"]
head_dict['avitus_head'] = ["avitus_head"]

backpack_dict = {}
backpack_dict['space_marine_backpack'] = ["space_marine_backpack"]
backpack_dict['assault_marine_jumppack'] = ["assault_marine_jumppack"]        
backpack_dict['gabriel_backpack'] = [("gabriel_backpack", "fc_backpack")]
backpack_dict['avitus_backpack'] = [("avitus_backpack", "space_marine_backpack")]

melee_weapon_dict = {}
melee_weapon_dict['power_axe_common'] = ["power_axe_common"]
melee_weapon_dict['chainsword_common'] = ["chainsword_common"]
melee_weapon_dict['power_fist_common'] = ["power_fist_common"]     
melee_weapon_dict['knife_common'] = ["knife_common"]    

melee_2h_weapon_dict = {}
melee_2h_weapon_dict['doublehand_hammer_common'] = ["doublehand_hammer_common"]

pistol_dict = {}
pistol_dict['bolt_pistol_common'] = ["bolt_pistol_common"] 
pistol_dict['plasma_pistol_common'] = ["plasma_pistol_common"]    

weapon_dict = {}
weapon_dict['bolter_common'] = ["bolter_common"]  
weapon_dict['heavy_bolter_common'] = ["heavy_bolter_common"] 
weapon_dict['flamer_common'] = ["flamer_common"]       
weapon_dict['lascannon_common'] = ["lascannon_common"]   
weapon_dict['meltagun_common'] = ["meltagun_common"]     
weapon_dict['missile_launcher_common'] = ["missile_launcher_common"]                
weapon_dict['plasma_cannon_common'] = ["plasma_cannon_common"]               
weapon_dict['plasma_gun_common'] = ["plasma_gun_common"]               

gear_list = [armour_dict, head_dict, backpack_dict, melee_weapon_dict, melee_2h_weapon_dict, pistol_dict, weapon_dict]     

unit_types = {}
unit_types['common'] = ['power_armour_rare', 'space_marine_head', 'space_marine_backpack', None, None, None, 'bolter_common']
unit_types['commander'] = ['power_armour_commander', 'gabriel_head', 'gabriel_backpack', None, 'doublehand_hammer_common', None, None]
unit_types['heavy'] = ['power_armour_rare', 'space_marine_head', 'space_marine_backpack', None, None, None, 'heavy_bolter_common']
unit_types['assault'] = ['power_armour_common', 'assault_marine_head', 'assault_marine_jumppack', 'power_axe_common', None, 'bolt_pistol_common', None]

anim_dict = {}
anim_dict['idle_stand01'] = 'idle_stand01'
anim_dict['idle_stand02'] = 'idle_stand02'
anim_dict['idle_stand03'] = 'idle_stand03'
anim_dict['idle_combat01'] = 'idle_combat_stand01'
anim_dict['idle_combat02'] = 'idle_combat_stand02'
anim_dict['idle_combat03'] = 'idle_combat_stand03'   
anim_dict['run'] = 'run' 
anim_dict['shoot'] = 'fire_stand'
anim_dict['damage'] = 'pinned_idle'
anim_dict['die'] = 'die_normal_f'
anim_dict['overwatch'] = 'aim_stand'
anim_dict['melee'] = 'melee_attack01'

unit_types = {}
unit_types['marine_common'] = ['space_marine_head', 'power_armour_common', 'space_marine_backpack', 'power_axe_common', 'bolt_pistol_common', None, None]
unit_types['marine_epic'] = ['gabriel_head', 'power_armour_commander', 'gabriel_backpack', 'power_axe_common', 'bolt_pistol_common', None, None]
unit_types['common'] = ['power_armour_rare', 'space_marine_head', 'space_marine_backpack', None, None, None, 'bolter_common']
unit_types['commander'] = ['power_armour_commander', 'gabriel_head', 'gabriel_backpack', None, 'doublehand_hammer_common', None, None]
unit_types['heavy'] = ['power_armour_rare', 'space_marine_head', 'space_marine_backpack', None, None, None, 'heavy_bolter_common']
unit_types['assault'] = ['power_armour_common', 'assault_marine_head', 'assault_marine_jumppack', 'power_axe_common', None, 'bolt_pistol_common', None]

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
    return angle

def loadUnit(unit_type):
    model = Actor('marine') 
    model.loadAnims(anim_dict)
    model.reparentTo(render)
    model.node_dict = {}
    for dict in gear_list:
        for g in dict.itervalues():
            for node in g:
                if isinstance(node, tuple):
                    model.node_dict[node[0]] = model.find("**/"+node[0])
                    if node[1]:
                        l = loader.loadTexture(node[1]+"_dif.dds")
                        model.node_dict[node[0]].setTexture(l)
                else:
                    model.node_dict[node] = model.find("**/"+node)
                    if node == 'bolter_common':
                        l=loader.loadTexture("bolter_common_dif.tga")
                    else:
                        l = loader.loadTexture(node+"_dif.dds")
                    model.node_dict[node].setTexture(l)
    initModels(model, unit_type)
    initAnims(model, unit_type)
    return model

def initModels(model, unit_type):
    for gear in gear_list:
        for item in gear.itervalues():
            for node in item:
                if isinstance(node, tuple):
                    n = node[0]
                else:
                    n = node
                model.node_dict[n] = model.find("**/"+n)
                if n not in unit_types[unit_type]:
                    model.node_dict[n].detachNode()
                    #model.node_dict[n].remove()
    
def initAnims(model, unit_type):
    model.anims = {}
    if unit_type == 'common':
        prefix = 'range_burst/'
    elif unit_type == 'commander':
        prefix = 'twohand_hammer/'
    elif unit_type == 'assault' or unit_type == 'marine_common' or unit_type == 'marine_epic':
        prefix = 'melee_axe_range_pistol/'
    elif unit_type == 'heavy':
        prefix = 'range_burst/'
    for anim in anim_dict.iterkeys():
        model.anims[anim] = prefix+anim_dict[anim]
    model.loadAnims(model.anims)

