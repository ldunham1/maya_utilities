from functools import partial, wraps

import maya.cmds as mc


GROUPMOVER_ID_ATTR = 'ld_group_mover'
GROUPMOVER_TGT_SOURCE_ATTR = 'ld_group_mover_source'


# ------------------------------------------------------------------------------
class UndoChunk(object):
    def __enter__(self):
        mc.undoInfo(ock=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        mc.undoInfo(cck=True)
        return False

    def __call__(self, func):
        @wraps(func)
        def decorated(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return decorated


# ------------------------------------------------------------------------------
def snap_objects(source, target):
    position = mc.xform(source, q=True, ws=True, t=True)
    rotation = mc.xform(source, q=True, ws=True, ro=True)
    mc.xform(target, ws=True, t=position, ro=rotation)


# ------------------------------------------------------------------------------
def find_group_movers():
    return mc.ls(
        '.' + GROUPMOVER_ID_ATTR,
        type='transform',
        objectsOnly=True,
        recursive=True,
    )


@UndoChunk()
def move(mover):
    to_delete = []
    for child in mc.listRelatives(mover, c=True, path=True):
        if not mc.attributeQuery(GROUPMOVER_TGT_SOURCE_ATTR, n=child, ex=True):
            continue

        target = mc.listConnections(child + '.' + GROUPMOVER_TGT_SOURCE_ATTR, destination=False)
        if not target:
            to_delete.append(child)
            continue

        position = mc.xform(child, q=True, ws=True, t=True)
        rotation = mc.xform(child, q=True, ws=True, ro=True)
        mc.xform(target, ws=True, t=position, ro=rotation)

    # Cleanup obsolete sources.
    if to_delete:
        mc.delete(to_delete)


def setup_callbacks(mover):
    mc.scriptJob(
        attributeChange=[mover + '.t', partial(move, mover)],
        parent=mover,
    )
    mc.scriptJob(
        attributeChange=[mover + '.r', partial(move, mover)],
        parent=mover,
    )
    mc.scriptJob(
        attributeChange=[mover + '.s', partial(move, mover)],
        parent=mover,
    )


# ------------------------------------------------------------------------------
def create_group_mover_source(node):
    group_mover = mc.createNode('transform', n=node + '__group_mover_tgt')
    mc.setAttr(group_mover + '.visibility', 0)

    mc.addAttr(group_mover, ln=GROUPMOVER_TGT_SOURCE_ATTR, at='message')
    mc.connectAttr(node + '.message', group_mover + '.' + GROUPMOVER_TGT_SOURCE_ATTR)

    return group_mover


def create_group_mover(node_list):
    group_mover, shape = mc.polyCube(n='group_mover_#')

    bb = mc.xform(node_list, q=True, bb=True)
    mc.setAttr(shape + '.width', bb[3] - bb[0] + 0.01)
    mc.setAttr(shape + '.height', bb[4] - bb[1] + 0.01)
    mc.setAttr(shape + '.depth', bb[5] - bb[2] + 0.01)

    for node in node_list:
        src = create_group_mover_source(node)
        mc.parent(src, group_mover)

    setup_callbacks(group_mover)

    return group_mover


def delete(movers=None):
    movers = movers or find_group_movers()
    if movers:
        mc.delete(movers)


def main():
    create_group_mover(mc.ls(sl=True))


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
