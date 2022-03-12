from functools import wraps
import logging

import maya.cmds as mc


__author__ = 'Lee Dunham'
__version__ = '0.1.2'


LOG = logging.getLogger('ld_see_me')
ELEMENT_PREFIX = 'LDSeeMe'
GROUP_NAME = ELEMENT_PREFIX + '_grp'
INSTANCE_SCALE = 0.5


class Optimise(object):
    def __enter__(self):
        mc.refresh(su=True)
        mc.undoInfo(openChunk=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        mc.undoInfo(closeChunk=True)
        mc.refresh(su=False)
        return False

    def __call__(self, func):
        @wraps(func)
        def decorator(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return decorator


# --------------------------------------------------------------------------
def get_selected_mesh_xforms():
    return list(filter(
        lambda x: mc.listRelatives(x, shapes=True, typ='mesh'),
        mc.ls(sl=True, typ='transform'),
    ))


def get_group():
    return mc.group(empty=True, name=GROUP_NAME)


def get_active_camera():
    return mc.modelEditor('modelPanel4', q=True, activeView=True, camera=True)


def create_instances(node_list, parent=None, count=4):
    results = []

    # Create an instance per corner
    for _ in range(count):
        duplicates = mc.duplicate(node_list, instanceLeaf=True, returnRootsOnly=True)
        if parent:
            duplicates = mc.parent(duplicates, parent)

        results.append(duplicates)

    return results


@Optimise()
def main():
    selection = get_selected_mesh_xforms()
    if not selection:
        LOG.error('Select at least 1 mesh.')
        return

    group = get_group()
    mc.select(group)
    layer = mc.createDisplayLayer(name=ELEMENT_PREFIX + '_lyr')
    mc.setAttr(layer + ".displayType", 2)

    camera = get_active_camera()
    mc.parentConstraint(camera, group, maintainOffset=True)

    create_instances(selection, parent=group)
    mc.setAttr(group + '.scale', INSTANCE_SCALE, INSTANCE_SCALE, INSTANCE_SCALE)

    mc.select(cl=True)


# --------------------------------------------------------------------------
if __name__ == '__main__':
    main()
