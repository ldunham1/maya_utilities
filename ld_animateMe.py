import maya.cmds as mc


version = (2, 1, 0)


class ldAnimateMe(object):
    WINDOW_NAME = 'ld_animateMe_win'

    def __init__(self):
        self.setupUi()

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


ldAnimateMe()
