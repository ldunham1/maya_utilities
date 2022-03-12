import json

import maya.cmds as mc


SHADER_MAPPING_NODE = 'ld_shader_mapping_node'
TRANSPARENT_SHADER_NAME = 'ld_transparencyShader'


# ------------------------------------------------------------------------------
def _get_shading_engine(node):
    for grp in mc.ls(type='shadingEngine'):
        if mc.sets(node, isMember=grp):
            return grp

    return None


# ------------------------------------------------------------------------------
def get_shader_mapping_node():
    if mc.objExists(SHADER_MAPPING_NODE):
        return SHADER_MAPPING_NODE

    mc.createNode('network', n=SHADER_MAPPING_NODE)
    mc.addAttr(SHADER_MAPPING_NODE, ln='shader_mapping', dt='string')
    return SHADER_MAPPING_NODE


def get_shader_mappings():
    node = get_shader_mapping_node()
    return json.loads(mc.getAttr(node + '.shader_mapping', type='string'))


def set_shader_mappings(data, update=False):

    if update:
        _data = get_shader_mappings()
        _data.update(data)
        data = _data

    node = get_shader_mapping_node()
    mc.setAttr(
        node + '.shader_mapping',
        json.dumps(data),
        type='string',
    )


def get_shader_mapping_for_node(node):
    data = get_shader_mappings()
    return data.get(node)


# ------------------------------------------------------------------------------
def toggle_transparency(object_list):
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
