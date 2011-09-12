from direct.actor.Actor import Actor

class UnitLoader:
    def load(self, type, buffer):
        if type == 'terminator':
            model = Actor('terminator', {'run': 'terminator-run'
                                        ,'idle02': 'terminator-run'
                                        })
        elif type == 'marine_b':
            model = Actor('marine_b',   {'run': 'marine-run'
                                        ,'idle02': 'marine-fire'
                                        })
        elif type == 'commissar':
            model = Actor('commissar', {'run': 'commissar-run'
                                       ,'idle01': 'commissar-idle1'
                                       ,'idle02': 'commissar-idle2'
                                       ,'idle03': 'commissar-idle3'
                                       ,'fire': 'commissar-fire'
                                       })
        
        if buffer != "off":
            model.setScale(0.25)
            # bake in rotation transform because model is created facing towards screen
            model.setH(180) 
            model.flattenLight()
        return model

class SoundLoader:
    def __init__(self):
        self.sounds = {}
        self.sounds['select0101'] = loader.loadSfx('sel0101.wav')
        self.sounds['select0102'] = loader.loadSfx('sel0102.wav')
        self.sounds['select0103'] = loader.loadSfx('sel0103.wav')
        self.sounds['select0104'] = loader.loadSfx('sel0104.wav')
        self.sounds['select0201'] = loader.loadSfx('sel0201.wav')
        self.sounds['select0202'] = loader.loadSfx('sel0202.wav')
        self.sounds['select0203'] = loader.loadSfx('sel0203.wav')
        self.sounds['select0204'] = loader.loadSfx('sel0204.wav')     
        
        self.sounds['movend0101'] = loader.loadSfx('movend0101.wav')
        self.sounds['movend0102'] = loader.loadSfx('movend0102.wav')
        self.sounds['movend0103'] = loader.loadSfx('movend0103.wav')
        self.sounds['movend0201'] = loader.loadSfx('movend0201.wav')
        self.sounds['movend0202'] = loader.loadSfx('movend0202.wav')
        self.sounds['movend0203'] = loader.loadSfx('movend0203.wav')
