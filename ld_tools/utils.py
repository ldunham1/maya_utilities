from functools import wraps

import maya.cmds as mc


# Python 2/3 compat
try:
    from contextlib import ContextDecorator as _ContextDecorator
except ImportError:
    class _ContextDecorator(object):
        """contextlib.ContextDecorator backport."""
        def __call__(self, func):
            @wraps(func)
            def decorated(*args, **kwargs):
                with self:
                    return func(*args, **kwargs)
            return decorated


# ------------------------------------------------------------------------------
class UndoChunk(_ContextDecorator):
    """Contain all scoped operations into single undo."""

    def __enter__(self):
        mc.undoInfo(openChunk=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        mc.undoInfo(closeChunk=True)
        return False


class SuspendRefresh(_ContextDecorator):
    """Suspend viewport update."""

    def __enter__(self):
        mc.refresh(suspend=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        mc.refresh(suspend=False)
        return False


class OptimiseContext(UndoChunk, SuspendRefresh):

    def __enter__(self):
        UndoChunk.__enter__(self)
        SuspendRefresh.__enter__(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        SuspendRefresh.__exit__(self, exc_type, exc_val, exc_tb)
        UndoChunk.__exit__(self, exc_type, exc_val, exc_tb)
        return False


# ------------------------------------------------------------------------------
def ensure_iterable(objects, accepted_types=(list, tuple, set)):
    if isinstance(objects, accepted_types):
        return objects
    elif not objects:
        return []

    return [objects]


# ------------------------------------------------------------------------------
def xform_snap(source, target, worldspace=True):
    position = mc.xform(source, q=True, ws=worldspace, sp=True)
    rotation = mc.xform(source, q=True, ws=worldspace, ro=True)
    mc.xform(target, ws=worldspace, t=position, ro=rotation)


def filter_by_shape(node_list, shape_types):
    return list(filter(
        lambda x: mc.listRelatives(x, shapes=True, typ=shape_types),
        node_list,
    ))


def get_active_camera():
    editor = mc.playblast(activeEditor=True)
    return mc.modelEditor(editor, q=True, activeView=True, camera=True)
