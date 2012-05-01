'''
Created on 15. tra. 2012.

@author: Vjeko
'''
'''
Created on 3. tra. 2012.

@author: Vjeko
'''
from panda3d.rocket import *
import traceback 

class LevelListDataSource(DataSource): 
    def __init__(self, name): 

        self.levels = []
        self.levels.append({'name':'assasins', 'size':'20x20', 'players':2, 'description':'description0Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins1', 'size':'21x20', 'players':2, 'description':'description1Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins2', 'size':'22x20', 'players':2, 'description':'description2Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins3', 'size':'23x20', 'players':2, 'description':'description3Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins4', 'size':'24x20', 'players':2, 'description':'description4Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins5', 'size':'25x20', 'players':4, 'description':'description5Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins6', 'size':'26x20', 'players':4, 'description':'description6Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins', 'size':'20x20', 'players':2, 'description':'description0Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins1', 'size':'21x20', 'players':2, 'description':'description1Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins2', 'size':'22x20', 'players':2, 'description':'description2Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins3', 'size':'23x20', 'players':2, 'description':'description3Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins4', 'size':'24x20', 'players':2, 'description':'description4Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins5', 'size':'25x20', 'players':4, 'description':'description5Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins6', 'size':'26x20', 'players':4, 'description':'description6Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins', 'size':'20x20', 'players':2, 'description':'description0Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins1', 'size':'21x20', 'players':2, 'description':'description1Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins2', 'size':'22x20', 'players':2, 'description':'description2Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins3', 'size':'23x20', 'players':2, 'description':'description3Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins4', 'size':'24x20', 'players':2, 'description':'description4Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins5', 'size':'25x20', 'players':4, 'description':'description5Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins6', 'size':'26x20', 'players':4, 'description':'description6Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins1', 'size':'21x20', 'players':2, 'description':'description1Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins2', 'size':'22x20', 'players':2, 'description':'description2Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins3', 'size':'23x20', 'players':2, 'description':'description3Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins4', 'size':'24x20', 'players':2, 'description':'description4Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins5', 'size':'25x20', 'players':4, 'description':'description5Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})
        self.levels.append({'name':'assasins6', 'size':'26x20', 'players':4, 'description':'description6Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'})

        
        DataSource.__init__(self, name) 


    def GetRow(self, table_name, index, columns): 
        row = list() 
        
        try: 
            if index > len(self.levels)-1: 
                return row 
                    
            if(table_name == 'levels'): 
                for col in columns: 
                    
                    if col not in self.levels[index]: 
                        continue # skip columns we don't know 
                    
                    if(col == 'name'): 
                        row.append(self.levels[index][col]) 

                    elif(col == 'size'): 
                        row.append(self.levels[index][col]) 

        except: 
            traceback.print_exc() 

        return row 
        
    def GetNumRows(self, table_name): 
        if(table_name == 'levels'): 
            return len(self.levels) 

        return 0 

class ArmySizeDataSource(DataSource): 
    def __init__(self, name): 

        self.size = []
        self.size.append({'size':500})
        self.size.append({'size':1000})
        self.size.append({'size':1500})
        
        DataSource.__init__(self, name) 


    def GetRow(self, table_name, index, columns): 
        row = list() 
        
        try: 
            if index > len(self.size)-1: 
                return row 
                    
            if(table_name == 'size'): 
                for col in columns: 
                    
                    if col not in self.size[index]: 
                        continue # skip columns we don't know 
                    
                    if(col == 'size'): 
                        row.append(self.size[index][col]) 
        except: 
            traceback.print_exc() 

        return row 
        
    def GetNumRows(self, table_name): 
        if(table_name == 'size'): 
            return len(self.size) 

        return 0 

class PlayerNumberDataSource(DataSource): 
    def __init__(self, name): 

        self.number = []
        self.number.append({'number':2})
        self.number.append({'number':3})
        self.number.append({'number':4})
        
        DataSource.__init__(self, name) 


    def GetRow(self, table_name, index, columns): 
        row = list() 
        
        try: 
            if index > len(self.number)-1: 
                return row 
                    
            if(table_name == 'number'): 
                for col in columns: 
                    
                    if col not in self.number[index]: 
                        continue # skip columns we don't know 
                    
                    if(col == 'number'): 
                        row.append(self.number[index][col]) 
        except: 
            traceback.print_exc() 

        return row 
        
    def GetNumRows(self, table_name): 
        if(table_name == 'number'): 
            return len(self.number) 

        return 0 
        
class GameTypeDataFormatter(DataFormatter): 
    def __init__(self, name): 
        
        DataFormatter.__init__(self, name) 

    def FormatData(self, inputstring):
        
        #out = "%-15s" % inputstring[0] + inputstring[1]
        #out = inputstring[0] + "-"*(15 - len(inputstring[0])) + inputstring[1]
        #print out
        return inputstring[0] + "  " + inputstring[1]
        
        
#hs = HighScoreDataSource("high_scores") 