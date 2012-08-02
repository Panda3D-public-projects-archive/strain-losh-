import sys
sys.path.append('./../client')
sys.path.append('./../client/strain')
sys.path.append('./src')
from engine import *
import sterner

#EngineThread().start()

sternerObj = sterner.Sterner()
sternerObj.start()
