'''
Created on 3. tra. 2012.

@author: Vjeko
'''
from panda3d.rocket import *
import traceback 

#unit_dict = {}
#unit_dict['NONE'] = {'name':'NONE', 'cost':0}
#unit_dict['Standard'] = {'name':'Standard', 'cost':100}
#unit_dict['Sergeant'] = {'name':'Sergeant', 'cost':150}
#unit_dict['Medic'] = {'name':'Medic', 'cost':100}
#unit_dict['Heavy'] = {'name':'Heavy', 'cost':100}
#unit_dict['Scout'] = {'name':'Scout', 'cost':100}
#unit_dict['Jumper'] = {'name':'Jumper', 'cost':100}


class SquadDataSource(DataSource): 
    def __init__(self, name, unit_dict): 
        self.squad = [] # could be any name 
        
        for key in unit_dict:
            if unit_dict[key]['cost'] == 0:
                self.squad.insert(0, {'name':unit_dict[key]['name'], 'cost':unit_dict[key]['cost']})
            else:
                self.squad.append({'name':unit_dict[key]['name'], 'cost':unit_dict[key]['cost']})

#        self.squad.append({'name':'NONE', 'cost':'0'})
#        self.squad.append({'name':'Standard', 'cost':'100'}) 
#        self.squad.append({'name':'Sergeant', 'cost':'150'}) 
#        self.squad.append({'name':'Medic', 'cost':'100'}) 
#        self.squad.append({'name':'Heavy', 'cost':'100'}) 
#        self.squad.append({'name':'Scout', 'cost':'100'}) 
#        self.squad.append({'name':'Jumper', 'cost':'100'})  
        
        DataSource.__init__(self, name) 


    def GetRow(self, table_name, index, columns): 
        row = list() 
        
        try: 
            if index > len(self.squad)-1: 
                return row 
                    
            if(table_name == 'squad'): 
                for col in columns: 
                    
                    if col not in self.squad[index]: 
                        continue # skip columns we don't know 
                    
                    if(col == 'name'): 
                        row.append(self.squad[index][col]) 

                    elif(col == 'cost'): 
                        row.append(self.squad[index][col]) 

        except: 
            traceback.print_exc() 

        return row 
        
    def GetNumRows(self, table_name): 
        if(table_name == 'squad'): 
            return len(self.squad) 

        return 0 

class SquadDataFormatter(DataFormatter): 
    def __init__(self, name): 
        
        DataFormatter.__init__(self, name) 

    def FormatData(self, inputstring):
        
        #out = "%-15s" % inputstring[0] + inputstring[1]
        #out = inputstring[0] + "-"*(15 - len(inputstring[0])) + inputstring[1]
        #print out
        return inputstring[0] + "  " + inputstring[1]
        
        
#hs = HighScoreDataSource("high_scores") 