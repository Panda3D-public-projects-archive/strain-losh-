from distutils.core import setup
import py2exe

setup(
    name = 'editor',
    description = 'mw editor',
    version = '1.0',

    windows = [
                  {
                      'script': './__init__.py',
#                      'icon_resources': [(1, "handytool.ico")],
                  }
              ],

    options = {
                  'py2exe': {
                      'packages':'encodings',
                      'includes': 'cairo, pango, pangocairo, atk, gobject',
                  }
              },

    data_files=[
                   'editor.glade'                   
               ]
)