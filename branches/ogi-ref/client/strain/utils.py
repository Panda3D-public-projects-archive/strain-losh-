#############################################################################
# IMPORTS
#############################################################################

# python imports

# panda3D imports
from pandac.PandaModules import GeomNode, NodePath

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

head_dict = {}
head_dict['space_marine_head'] = ["space_marine_head"]
head_dict['assault_marine_head'] = ["assault_marine_head"]        
head_dict['gabriel_head'] = [("gabe_head", "gabriel_head")]
head_dict['avitus_head'] = ["avitus_head"]

armour_dict = {}
armour_dict['power_armour_common'] = ["power_armour_common"]
armour_dict['power_armour_rare'] = ["power_armour_rare"]
armour_dict['power_armour_epic'] = ["power_armour_epic"]
armour_dict['power_armour_commander'] = ["power_armour_commander"]
armour_dict['power_armour_cuirass_of_azariah'] = ["power_armour_cuirass_of_azariah"]
armour_dict['power_armour_gabriel'] = ["power_armour_gabriel"]
armour_dict['power_armour_of_the_destroyer'] = ["power_armour_of_the_destroyer", ("power_armour_of_the_destroyer_acc", "accessories_destroyer")]
armour_dict['power_armour_mantle_great_father'] = ["power_armour_mantle_great_father", ("power_armour_mantle_great_father_acc", "assault_accessories")]
armour_dict['power_armour_of_vandea'] = [("power_armour_of_vandea1", "power_armour_of_vandea"), ("power_armour_of_vandea2", "power_armour_of_vandea"), ("power_armour_of_vandea_acc", "vandea_accessories")]
armour_dict['power_armour_raven'] = [("power_armour_raven", "power_armour_raven_barding_flight"), ("power_armour_raven_laurels", "iron_halo_laurels_of_hadrian"), ("power_armour_raven_acc", "assault_accessories")]

backpack_dict = {}
backpack_dict['space_marine_backpack'] = ["space_marine_backpack"]
backpack_dict['assault_marine_jumppack'] = ["assault_marine_jumppack"]        
backpack_dict['gabriel_backpack'] = [("gabe_backpack", "fc_backpack")]
backpack_dict['avitus_backpack'] = [("avitus_backpack", "space_marine_backpack")]

melee_weapon_dict = {}
melee_weapon_dict['power_axe_common'] = ["power_axe_common"]
melee_weapon_dict['power_axe_rare'] = ["power_axe_rare"]
melee_weapon_dict['power_axe_epic'] = ["power_axe_epic"]
melee_weapon_dict['power_axe_rounded'] = ["power_axe_rounded"]
melee_weapon_dict['power_axe_black'] = ["power_axe_black", ("power_axe_black_laurels", None)]
melee_weapon_dict['chainsword_common'] = ["chainsword_common"]
melee_weapon_dict['chainsword_rare'] = ["chainsword_rare"]
melee_weapon_dict['chainsword_epic'] = ["chainsword_epic"]
melee_weapon_dict['chainsword_black_rage'] = [("chainsword_black_rage", None)]
melee_weapon_dict['chainsword_blade_of_ulyus'] = [("chainsword_blade_of_ulyus", None)]
melee_weapon_dict['chainsword_snarl_of_the_wolf'] = ["chainsword_snarl_of_the_wolf"]
melee_weapon_dict['power_fist_common'] = ["power_fist_common"]
melee_weapon_dict['power_fist_rare'] = ["power_fist_rare"]
melee_weapon_dict['power_fist_epic'] = ["power_fist_epic"]        
melee_weapon_dict['power_fist_black'] = ["power_fist_black", ("power_fist_black_laurels", None)]        
melee_weapon_dict['power_fist_platinum'] = ["power_fist_platinum", ("power_fist_platinum_laurels", None)]      
melee_weapon_dict['power_fist_gauntlet_of_blood'] = ["power_fist_gauntlet_of_blood"]         
melee_weapon_dict['knife_common'] = ["knife_common"]    
melee_weapon_dict['knife_rare'] = ["knife_rare"]   
melee_weapon_dict['knife_epic'] = ["knife_epic"]  

pistol_dict = {}
pistol_dict['bolt_pistol_common'] = ["bolt_pistol_common"]
pistol_dict['bolt_pistol_rare'] = ["bolt_pistol_rare"]
pistol_dict['bolt_pistol_epic'] = ["bolt_pistol_epic"]
pistol_dict['bolt_pistol_comming_doom'] = ["bolt_pistol_coming_doom"]    
pistol_dict['bolt_pistol_of_baal'] = ["bolt_pistol_of_baal"]    
pistol_dict['plasma_pistol_common'] = ["plasma_pistol_common"] 
pistol_dict['plasma_pistol_rare'] = ["plasma_pistol_rare"] 
pistol_dict['plasma_pistol_epic'] = ["plasma_pistol_epic"] 

melee_2h_weapon_dict = {}
melee_2h_weapon_dict['doublehand_hammer_common'] = ["doublehand_hammer_common"]
melee_2h_weapon_dict['doublehand_hammer_rare'] = ["doublehand_hammer_rare"]
melee_2h_weapon_dict['doublehand_hammer_epic'] = ["doublehand_hammer_epic"]

weapon_dict = {}
weapon_dict['bolter_common'] = ["bolter_common"]  
weapon_dict['bolter_rare'] = ["bolter_rare"] 
weapon_dict['bolter_epic'] = ["bolter_epic"] 
weapon_dict['bolter_unforgiving_truth'] = [("bolter_unforgiving_truth", None), ("bolter_unforgiving_truth_sniper", None)] 
weapon_dict['flamer_common'] = ["flamer_common"]      
weapon_dict['flamer_rare'] = ["flamer_rare"]  
weapon_dict['flamer_epic'] = ["flamer_epic"]     
weapon_dict['flamer_purity_seal'] = ["flamer_purity_seal", ("flamer_purity_seal_seals", None)]     
weapon_dict['flamer_winged_skull'] = ["flamer_winged_skull", ("flamer_winged_skull2", None), ("flamer_winged_skull_seals", None)]
weapon_dict['heavy_bolter_common'] = ["heavy_bolter_common"]    
weapon_dict['heavy_bolter_rare'] = ["heavy_bolter_rare"]   
weapon_dict['heavy_bolter_epic'] = ["heavy_bolter_epic"]   
weapon_dict['heavy_bolter_purge_of_victory_bay'] = ["heavy_bolter_purge_of_victory_bay", ("heavy_bolter_purge_of_victory_bay_halo", None), ("heavy_bolter_purge_of_victory_bay_bauble", None), ("heavy_bolter_purge_of_victory_bay_seals", None)]          
weapon_dict['heavy_bolter_scourge_of_xenos'] = ["heavy_bolter_scourge_of_xenos", ("heavy_bolter_scourge_of_xenos_seals", None), ("heavy_bolter_scourge_of_xenos_halo", None)]          
weapon_dict['lascannon_common'] = ["lascannon_common"]   
weapon_dict['meltagun_common'] = ["meltagun_common"]     
weapon_dict['missile_launcher_common'] = ["missile_launcher_common"]       
weapon_dict['missile_launcher_rare'] = ["missile_launcher_rare"] 
weapon_dict['missile_launcher_epic'] = ["missile_launcher_epic"]   
weapon_dict['missile_launcher_unerring_thunderbolt'] = ["missile_launcher_unerring_thunderbolt", ("missile_launcher_unerring_thunderbolt2", None)]          
weapon_dict['plasma_cannon_common'] = ["plasma_cannon_common"]          
weapon_dict['plasma_cannon_epic'] = ["plasma_cannon_epic"] 
weapon_dict['plasma_cannon_gold'] = ["plasma_cannon_gold", ("plasma_cannon_gold_seals", None), ("plasma_cannon_gold_laurels", None)] 
weapon_dict['plasma_cannon_red'] = ["plasma_cannon_red", ("plasma_cannon_red_halo", None), ("plasma_cannon_red_seals", None)]       
weapon_dict['plasma_gun_common'] = ["plasma_gun_common"]   
weapon_dict['plasma_gun_rare'] = ["plasma_gun_rare"] 
weapon_dict['plasma_gun_epic'] = ["plasma_gun_epic"]       
weapon_dict['plasma_gun_light_of_faith'] = ["plasma_gun_light_of_faith", "plasma_gun_light_of_faith_baubles"]       
weapon_dict['plasma_gun_purifier_of_tombs'] = ["plasma_gun_purifier_of_tombs", "plasma_gun_purifier_of_tombs_baubles"]         

gear_list = [head_dict, armour_dict, backpack_dict, melee_weapon_dict, pistol_dict, melee_2h_weapon_dict, weapon_dict]     

anim_dict = {}
anim_dict['run'] = "run"
anim_dict['idle_stand01'] = "idle_stand01"

unit_types = {}
unit_types['marine_common'] = ['space_marine_head', 'power_armour_common', 'space_marine_backpack', 'power_axe_common', 'bolt_pistol_common', None, None]

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

