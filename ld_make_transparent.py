import maya.cmds as mc


TRANSPARENT_SHADER_NAME = 'ld_transparencyShader'


# ------------------------------------------------------------------------------
def _get_shading_engine(node):
    for grp in mc.ls(type='shadingEngine'):
        if mc.sets(node, isMember=grp):
            return grp

    return None


# ------------------------------------------------------------------------------
def make_transparent(object_list):
    """
    Toggle the transparency of objects or components.

    :return: None
    """
    object_list = object_list or mc.ls(sl=True)
    if not object_list:
        return

    shader = TRANSPARENT_SHADER_NAME

    if not mc.objExists(shader):
        mc.shadingNode('lambert', asShader=True, n=shader)
        mc.setAttr(shader + '.transparency', 1, 1, 1)

    mc.select(object_list)
    mc.hyperShade(assign=shader)
