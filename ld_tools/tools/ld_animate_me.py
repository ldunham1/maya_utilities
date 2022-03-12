from functools import wraps
import logging

import maya.cmds as mc


__author__ = 'Lee Dunham'
__version__ = '3.0.0'


LOG = logging.getLogger('ld_animate_me')


# ------------------------------------------------------------------------------
class OptimiseContext(object):

    def __enter__(self):
        mc.undoInfo(openChunk=True)
        mc.refresh(suspend=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        mc.undoInfo(closeChunk=True)
        mc.refresh(suspend=False)
        return False

    def __call__(self, func):
        @wraps(func)
        def decorated(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return decorated


# ------------------------------------------------------------------------------
class LDAnimateMeUi(object):
    WINDOW_NAME = 'ld_animateMe_win'

    def __init__(self):
        self.setupUi()
        self.show()

    def exists(self):
        return mc.window(self.WINDOW_NAME, ex=True)

    def close(self):
        if self.exists():
            mc.deleteUI(self.WINDOW_NAME)

    def show(self):
        if self.exists():
            mc.showWindow(self.WINDOW_NAME)

    def setupUi(self):

        self.close()

        mc.window(
            self.WINDOW_NAME,
            t='{} v{}'.format(' '.join(self.WINDOW_NAME.split('_')[:-1]).title(), version),
            w=400,
            h=300,
        )

        layout = mc.columnLayout(adj=True)
        mc.frameLayout()
        mc.setParent('..')
        mc.setParent('..')


# ------------------------------------------------------------------------------
def launch():
    ui = LDAnimateMeUi()
    return ui


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    launch()

