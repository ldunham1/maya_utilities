import logging

import maya.cmds as mc

from .. import utils


__author__ = 'Lee Dunham'
__version__ = '0.1.3'


LOG = logging.getLogger('ld_see_me')
ELEMENT_PREFIX = 'LDSeeMe'
GROUP_NAME = ELEMENT_PREFIX + '_grp'
INSTANCE_SCALE = 0.5


# --------------------------------------------------------------------------
def get_group():
    return mc.group(empty=True, name=GROUP_NAME)


def create_instances(node_list, parent=None, count=4):
    results = []

    # Create an instance per corner
    for _ in range(count):
        duplicates = mc.duplicate(node_list, instanceLeaf=True, returnRootsOnly=True)
        if parent:
            duplicates = mc.parent(duplicates, parent)

        results.append(duplicates)

    return results


@utils.OptimiseContext()
def main():
    selection = utils.filter_by_shape(mc.ls(typ='transform'), 'mesh')
    if not selection:
        LOG.error('Select at least 1 mesh.')
        return

    group = get_group()
    mc.select(group)
    layer = mc.createDisplayLayer(name=ELEMENT_PREFIX + '_lyr')
    mc.setAttr(layer + ".displayType", 2)

    camera = utils.get_active_camera()
    mc.parentConstraint(camera, group, maintainOffset=True)

    create_instances(selection, parent=group)
    mc.setAttr(group + '.scale', INSTANCE_SCALE, INSTANCE_SCALE, INSTANCE_SCALE)

    mc.select(cl=True)


# --------------------------------------------------------------------------
if __name__ == '__main__':
    main()
