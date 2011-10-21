class SoundLoader:
    def __init__(self, ge):
        self.sounds = {}
        self.sounds['select0101'] = ge.loader.loadSfx('sel0101.wav')
        self.sounds['select0102'] = ge.loader.loadSfx('sel0102.wav')
        self.sounds['select0103'] = ge.loader.loadSfx('sel0103.wav')
        self.sounds['select0104'] = ge.loader.loadSfx('sel0104.wav')
        self.sounds['select0201'] = ge.loader.loadSfx('sel0201.wav')
        self.sounds['select0202'] = ge.loader.loadSfx('sel0202.wav')
        self.sounds['select0203'] = ge.loader.loadSfx('sel0203.wav')
        self.sounds['select0204'] = ge.loader.loadSfx('sel0204.wav')     
        
        self.sounds['movend0101'] = ge.loader.loadSfx('movend0101.wav')
        self.sounds['movend0102'] = ge.loader.loadSfx('movend0102.wav')
        self.sounds['movend0103'] = ge.loader.loadSfx('movend0103.wav')
        self.sounds['movend0201'] = ge.loader.loadSfx('movend0201.wav')
        self.sounds['movend0202'] = ge.loader.loadSfx('movend0202.wav')
        self.sounds['movend0203'] = ge.loader.loadSfx('movend0203.wav')
