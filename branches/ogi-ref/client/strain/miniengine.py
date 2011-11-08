class MiniEngine():
    def __init__(self, ge):
        self.ge = ge
        self.level = None
    
    def outOfLevelBounds(self, x, y):
        if(x < 0 or y < 0 or x >= self.level['maxX'] or y >= self.level['maxY']):
            return True
        else:
            return False

    def canIMoveHere(self, unit, position, dx, dy):
        dx = int(dx)
        dy = int(dy)
              
        if( (dx != 1 and dx != 0 and dx != -1) and 
            (dy != 1 and dy != 0 and dy != -1) ):
            print ( "Invalid dx (%d) or dy (%d)" %(dy ,dy) )
        
        ptx = int(position[0])
        pty = int(position[1])
        
        if self.outOfLevelBounds(ptx+dx, pty+dy):
            return False

        #check if the level is clear at that tile
        if(self.level['_level_data'][ptx + dx][pty + dy] != 0):
            return False
        
        #check if there is a dynamic obstacle in the way
        if self.ge.unit_np_list[ptx+dx][pty+dy]:
            return False
        """
        if( self.dynamic_obstacles[ ptx + dx ][ pty + dy ][0] != DYNAMICS_EMPTY ):
            #ok if it a unit, it may be the current unit so we need to check that
            if( self.dynamic_obstacles[ ptx + dx ][ pty + dy ][0] == DYNAMICS_UNIT ):
                if( self.dynamic_obstacles[ ptx + dx ][ pty + dy ][1] != unit.id ):
                    return False
        """
        
        #check diagonal if it is clear
        if( dx != 0 and dy != 0 ):
            
            #if there is something in level in the way
            if( self.level['_level_data'][ ptx + dx ][ pty ] != 0 or 
                self.level['_level_data'][ ptx ][ pty + dy ] != 0 ):
                return False
        
            #check if there is a dynamic thing in the way 
            """
            if( self.dynamic_obstacles[ ptx + dx ][ pty ][0] != DYNAMICS_EMPTY ):
                #see if it is a unit
                if( self.dynamic_obstacles[ ptx + dx ][ pty ][0] == DYNAMICS_UNIT ):
                    #so its a unit, see if it is friendly
                    unit_id = self.dynamic_obstacles[ ptx + dx ][ pty ][1] 
                    if( self.units[unit_id].owner != unit.owner ):
                        return False
                    
            if( self.dynamic_obstacles[ ptx ][ pty + dy ][0] != DYNAMICS_EMPTY ):
                if( self.dynamic_obstacles[ ptx ][ pty + dy ][0] == DYNAMICS_UNIT ):
                    unit_id = self.dynamic_obstacles[ ptx ][ pty + dy ][1] 
                    if( self.units[unit_id].owner != unit.owner ):
                        return False
            """
            
        return True
        
    def getMoveDict(self, unit, returnOrigin=False):    
        final_dict = {}
        open_list = [(unit['pos'], unit['ap'])]
        for tile, actionpoints in open_list:
            for dx in xrange(-1,2):
                for dy in xrange( -1,2 ):            
                    if( dx == 0 and dy == 0):
                        continue
                    #we can't check our starting position
                    if( tile[0] + dx == unit['pos'][0] and tile[1] + dy == unit['pos'][1] ):
                        continue
                    x = int( tile[0] + dx )
                    y = int( tile[1] + dy )
                    if self.outOfLevelBounds(x, y):
                        continue
                    if not self.canIMoveHere(unit, tile, dx, dy):
                        continue                   
                    #if we are checking diagonally
                    if( dx == dy or dx == -dy ):
                        ap = actionpoints - 1.5
                    else:
                        ap = actionpoints - 1
                    
                    if( ap < 0 ):
                        continue
                    
                    pt = (x,y) 
                    
                    if pt in final_dict:
                        if( final_dict[pt] < ap ):
                            final_dict[pt] = ap
                            open_list.append( ( pt, ap ) )
                    else: 
                            final_dict[pt] = ap
                            open_list.append( ( pt, ap ) )
        if( returnOrigin ):
            final_dict[unit.pos] = unit.ap
            return final_dict
        
        return final_dict