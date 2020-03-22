import logging

import maya.cmds as mc
import maya.mel as mm


__author__ = 'Lee Dunham'
__version__ = '1.5.0'


log = logging.getLogger('ld_select_me')


# ------------------------------------------------------------------------------
class DataHandler(object):
    def create(self, array_field, text_field):
        node_list = mc.textScrollList(array_field, q=True, ai=True) or mc.ls(sl=True)
        set_name = mc.textField(text_field, q=True, tx=True)
        if not node_list:
            log.error('No objects to create set.')

        ns = ''
        namespaces = node_list[0].split(':')
        if len(namespaces) > 1:
            ns = ':'.join(namespaces[:-1]) + ':'

        controls = [
            node.rsplit(':', 1)[-1]
            for node in node_list[:-2]
        ]
        data = [
            'import maya.cmds as mc',
            'nsBU = ns = "{namespace}"',
            'node_list = {controls}',
            'selection = mc.ls(sl=True)',
            'if selection:',
            '    currNs = selection[0].split(":")',
            '    if len(currNs) > 1:',
            '        ns = ":".join(currNs[:-1]) + ":"',
            'node_list = [(ns + item) for item in node_list]',
            'if mc.getModifiers() == 4:',
            '    mc.select(node_list, tgl=True)',
            'else:',
            '    mc.select(node_list)',
        ]
        data = '\n'.join(data).format(namespace=ns, controls=controls)
        self.addToShelf(set_name, data, 'python', set_name)

    def addToShelf(self, label, data, type='mel', annotation=''):
        shelf = mm.eval('global string $gShelfTopLevel; $return = $gShelfTopLevel')
        io_label = label
        if len(label) > 5:
            io_label = label[:5]

        if mc.tabLayout(shelf, ex=1):
            current_shelf = '%s|%s' % (shelf, mc.tabLayout(shelf, q=1, st=1))
            button = mc.shelfButton(
                label=label,
                iol=io_label,
                stp=type,
                rpt=1,
                i1='commandButton.png',
                ann=annotation,
                c=data,
                p=current_shelf,
            )
            mc.shelfButton(button, e=True, label=label)
            log.info('Shelf button "{}" added!!'.format(label))


# ------------------------------------------------------------------------------
class SelectMeUi(object):
    win_name = 'ld_selSets_win'

    def __init__(self):
        self.dh = DataHandler()
        self.close()
        self.setupUi()
        self.show()

    # --------------------------------------------------------------------------
    def add(self, field):
        selection = mc.ls(sl=True)
        if selection is None:
            log.warning('Nothing selected')

        current_list = mc.textScrollList(field, q=True, ai=True)
        if current_list is None:
            new_list = selection

        else:
            new_list = set(current_list + selection)

        mc.textScrollList(field, e=True, ra=True)
        for item in new_list:
            mc.textScrollList(field, e=True, a=item)

    def remove(self, field):
        node_list = mc.textScrollList(field, q=True, si=True)
        for node in node_list:
            mc.textScrollList(field, e=True, ri=node)

    def clear(self, field):
        mc.textScrollList(field, e=True, ra=True)

    def select(self, field):
        mc.select(mc.textScrollList(field, q=True, si=True))

    # --------------------------------------------------------------------------
    def close(self):
        if mc.window(self.win_name, ex=True):
            mc.deleteUI(self.win_name)

    def show(self):
        if mc.window(self.win_name, ex=True):
            mc.showWindow(self.win_name)

    # --------------------------------------------------------------------------
    def setupUi(self):
        title = 'SelectMe'
        mc.window(
            self.win_name,
            t=title,
            rtf=1,
            wh=[225, 250],
        )
        mc.paneLayout(
            cn='horizontal3',
            ps=[[1, 100, 1], [2, 100, 98], [3, 100, 1]],
            shp=1,
        )
        mc.columnLayout(adj=True)
        mc.text(label='Selection Sets')
        mc.separator(style='in')
        mc.rowLayout(nc=5, adj=2)
        mc.text(label=' Label:', w=35)
        mc.textField('ld_selSets_name_tField', ann='Button name, first 5 characters used as icon label', w=100)
        mc.button(label='clear', w=50, c=lambda *args: self.clear('ld_selSets_objs_tsList'))
        mc.columnLayout()
        mc.button(label='+', w=25, h=15, c=lambda *args: self.add('ld_selSets_objs_tsList'))
        mc.button(label='-', w=25, h=15, c=lambda *args: self.remove('ld_selSets_objs_tsList'))
        mc.setParent('..')
        mc.setParent('..')
        mc.setParent('..')
        mc.textScrollList(
            'ld_selSets_objs_tsList',
            w=150,
            h=75,
            ams=1,
            sc=lambda *_: self.select('ld_selSets_objs_tsList'),
            dkc=lambda *_: self.remove('ld_selSets_objs_tsList'),
        )
        mc.button(
            label='Create Selection Set',
            h=30,
            c=lambda *_: self.dh.create('ld_selSets_objs_tsList', 'ld_selSets_name_tField')
        )
        mc.setParent('..')


# ------------------------------------------------------------------------------
def launch():
    ui = SelectMeUi()
    return ui


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    launch()
