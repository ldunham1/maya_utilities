"""
Quickly mirror various objects, nurbs-curves, geo and deformers to speed up workflow.

Updates:

    09/03/2012 - 0.5.0
        Initial working version.

    10/03/12 - 0.9.5
        Tidied UI and reduced/cleaned code.

    13/03/12 - 1.0.0
        Added colour option for curves.
        Removed all pymel (speed issues).
        Allowed multi-mirroring.

    14/03/12 - 1.5.0
        Thanks to Matt Murray for feedback for further improvements.
        Added option to mirror world position of mirrored curve.
        Added further error-checking for all modes.
        Fixed bug causing unwanted locking of attributes.
            Added option to disable colouring of mirrored curve.

Usage with UI:

    >>> import ld_mirror_me
    >>> ld_mirror_me.launch()

"""
from functools import wraps
import logging

import maya.cmds as mc
import maya.mel as mm


__author__ = 'Lee Dunham'
__version__ = '2.0.1'


LOG = logging.getLogger('ld_mirror_me')


# ------------------------------------------------------------------------------
class OptimiseContext(object):

    def __enter__(self):
        mc.undoInfo(openChunk=True)
        mc.refresh(suspend=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        mc.undoInfo(closeChunk=True)
        mc.refresh(suspend=False)
        return False

    def __call__(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            with self:
                return f(*args, **kwargs)

        return decorated


# ------------------------------------------------------------------------------
def get_deformer_info(handle):
    """
    Return the vertices and weights for the deformer.

    :param handle: Deformer handle object.
    :type handle: str

    :return: list(list(str, float))
    """
    deformer = mc.listConnections(handle + '.worldMatrix[0]', type='cluster', d=True)[0]
    obj_set = mc.listConnections(deformer, type='objectSet')[0]
    components = mc.filterExpand(mc.sets(obj_set, q=True), sm=(28, 31, 36, 46))
    results = [
        [vertex, mc.percent(deformer, vertex, q=True, v=True)[0]]
        for vertex in components
    ]
    return results


def get_deformer_info_by_node(node, handle):
    deformer_info = get_deformer_info(handle)
    results = [
        data
        for data in deformer_info
        if data[0].startswith(node)
    ]
    return results


# ------------------------------------------------------------------------------
@OptimiseContext()
def shapeMirror(shape_list, position, axis, search, replace):

    if not isinstance(shape_list, (list, tuple, set)):
        shape_list = [shape_list]

    for shape in shape_list:
        if not mc.listRelatives(shape, shapes=True, type='nurbsCurve'):
            LOG.warning('Current version only supports nurbs curve.')
            continue

        orig_pos = mc.xform(shape, q=True, ws=True, rp=True)
        orig_rot = mc.xform(shape, q=True, ws=True, ro=True)

        mc.move(0, 0, 0, shape, ws=True)
        mc.rotate(0, 0, 0, shape, ws=True)
        curve_target = mc.duplicate(shape, returnRootsOnly=True)[0]
        for i in range(mc.getAttr(shape + '.spans')):
            pos = mc.xform((shape + '.cv[%s]' % i), q=True, ws=True, t=True)
            pos[axis] *= -1
            mc.move(pos[0], pos[1], pos[2], curve_target + '.cv[%s]' % i, ws=True)

        mc.move(orig_pos[0], orig_pos[1], orig_pos[2], shape, ws=True)
        mc.rotate(orig_rot[0], orig_rot[1], orig_rot[2], shape, ws=True)
        if mc.listRelatives(shape, parent=True):
            mc.parent(curve_target, world=True)

        if position == 2:
            mc.move(orig_pos[0], orig_pos[1], orig_pos[2], curve_target, ws=True)
            mc.rotate(orig_rot[0], orig_rot[1], orig_rot[2], curve_target, ws=True)

        elif position == 3:
            mirrored_pos = list(orig_pos)
            mirrored_pos[axis] *= -1
            mc.move(mirrored_pos[0], mirrored_pos[1], mirrored_pos[2], curve_target, ws=True)

        if mc.checkBox('ld_mCurve_colour_cBox', q=True, value=True) == 1:
            if mc.getAttr(mc.listRelatives(shape, shapes=True)[0] + '.overrideEnabled'):
                colour_object = mc.listRelatives(curve_target, shapes=True)[0] + '.overrideColor'

            else:
                colour_object = curve_target + '.overrideColor'

            value = mc.colorIndexSliderGrp('ld_mCurve_colour_cISGrp', q=True, value=True) - 1
            mc.setAttr(colour_object, value)

        mc.rename(curve_target, shape.replace(search, replace))


@OptimiseContext()
def meshMirror(original, target_list, position, axis, search, replace):
    if not isinstance(target_list, (list, tuple, set)):
        target_list = [target_list]

    attr_list = ['tx', 'ty', 'tz',
                 'rx', 'ry', 'rz',
                 'sx', 'sy', 'sz']

    for target in target_list:
        locked_attrs = []

        for attr in attr_list:
            lock_state = mc.getAttr(original + '.' + attr, lock=True)
            if lock_state:
                mc.setAttr(original + '.' + attr, lock=False)
                locked_attrs.append(attr)

        # Rename duplicated object
        scale_obj = mc.duplicate(original, returnRootsOnly=True)[0]
        mirror_obj = mc.duplicate(original, returnRootsOnly=True, n=target + 'suffTemp')[0]
        for attr in locked_attrs:
            mc.setAttr(original + '.' + attr, lock=True)

        mc.setAttr(
            scale_obj + '.' + attr_list[axis + 5],
            -1 * mc.getAttr(scale_obj + '.' + attr_list[axis + 5]),
        )

        # Create inverted blendshape and wrap
        blendshape = mc.blendShape(target, scale_obj, frontOfChain=True)[0]
        mc.select(mirror_obj, scale_obj, r=True)
        wrap = mm.eval('doWrapArgList "6" {"1","0","1","2","1","1","0"};')[0]
        mc.setAttr(wrap + '.exclusiveBind', 1)
        mc.setAttr(blendshape + '.' + target, 1)

        # Clean up
        mc.delete(mirror_obj, ch=True)
        mc.delete(scale_obj + 'Base', scale_obj)
        if position == 1:
            mc.setAttr(mirror_obj + '.t', *mc.getAttr(target + '.t')[0])

        mirror = mirror_obj.replace(search, replace).replace('suffTemp', '')
        mc.rename(mirror_obj, mirror)


@OptimiseContext()
def deformerMirror(node, handle_list, axis, search, replace):

    if not isinstance(handle_list, (list, tuple, set)):
        handle_list = [handle_list]

    for handle in handle_list:
        if not mc.listRelatives(handle, shapes=True, type='clusterHandle'):
            LOG.warning('Current version only supports Cluster deformers.')
            continue

        shapes = mc.listRelatives(node, shapes=True)
        current_data = get_deformer_info_by_node(node, handle)

        closest_point_node = mc.createNode('closestPointOnMesh')
        for data in current_data:
            point_pos = mc.pointPosition(data[0], local=True)
            inv_pos = point_pos
            inv_pos[axis] *= -1
            mc.setAttr(node + '.inPosition', *inv_pos)
            mc.connectAttr(shapes[0] + '.outMesh', closest_point_node + '.inMesh', force=True)
            closest_index = mc.getAttr(closest_point_node + '.closestVertexIndex')
            data[0] = node + '.vtx[{}]'.format(closest_index)

        mc.delete(closest_point_node)

        amount = len(current_data)
        new_points = [current_data[x][0] for x in range(amount)]
        deformer = mc.listConnections(handle + '.worldMatrix[0]', type='cluster', d=True)
        new_cluster = mc.cluster(new_points, rel=mc.getAttr(deformer + '.relative'))
        for x in range(amount):
            mc.percent(new_cluster[0], current_data[x][0], v=current_data[x][1])

        # Mirror deformer pivot
        a_pos = mc.xform(node, q=True, ws=True, rp=True)
        pos = b_pos = mc.xform(handle, q=True, ws=True, rp=True)
        pos[axis - 1] = b_pos[axis - 1] - ((b_pos[axis - 1] - a_pos[axis - 1]) * 2)
        mc.xform(new_cluster[1], a=True, ws=True, piv=(pos[0], pos[1], pos[2]))
        mc.setAttr(new_cluster[0] + '.origin', pos[0], pos[1], pos[2])
        mc.rename(new_cluster[1], handle.replace(search, replace))


# ------------------------------------------------------------------------------
class LDMirrorMeUi(object):
    win_name = 'ld_mirrorMe_win'

    MODE_SHAPE = 1
    MODE_MESH = 2
    MODE_DEFORMER = 3

    def __init__(self):
        self.close()
        self.setupUi()
        self.show()

    # --------------------------------------------------------------------------
    def switchLayouts(self, mode):
        all_modes = [1, 2, 3]
        all_modes.remove(mode)
        for m in all_modes:
            mc.frameLayout('ld_mMode%s_fLayout' % m, e=True, m=False)

        mc.frameLayout('ld_mMode%s_fLayout' % mode, e=True, m=True)

    def switchMode(self):
        self.switchLayouts(mc.radioButtonGrp('ld_mirrorMode_rBGrp', q=True, sl=True))

    def addToField(self, field, multi):
        objects = mc.ls(sl=True, objectsOnly=True)
        if not objects:
            LOG.warning('No objects selected!')
            return

        data = ', '.join(objects) if multi else objects[0]
        mc.textField(field, e=True, tx=data)

    # --------------------------------------------------------------------------
    @classmethod
    def _get_shape_type(cls, node):
        return mc.nodeType(mc.listRelatives(node, shapes=True)[0])

    @classmethod
    def _get_component_count(cls, node):
        node_type = cls._get_shape_type(node)
        if node_type == 'mesh':
            return mc.polyEvaluate(node, v=True)

        elif node_type in ('nurbsCurve', 'nurbsSurface'):
            shape = mc.listRelatives(node, shapes=True)[0]
            return mc.getAttr(shape + '.spansU') + mc.getAttr(shape + '.spansV')

        return None

    # --------------------------------------------------------------------------
    def applyShapeMirror(self, original, position, axis, search, replace):
        if not original:
            return

        shape_list = [
            shape.strip()
            for shape in original.split(',')
        ]
        shapeMirror(
            shape_list,
            position,
            axis=axis,
            search=search,
            replace=replace,
        )

    def applyMeshMirror(self, original, target_str, position, axis, search, replace):
        if not original or not target_str:
            return

        node_type = self._get_shape_type(original)
        orig_count = self._get_component_count(original)
        target_list = []
        for target in target_str.split(','):
            target = target.strip()
            if self._get_shape_type(target) != node_type:
                LOG.warning('"{}" is not the same type as "{}"!'.format(target, original))
                continue

            if self._get_component_count(target) != orig_count:
                LOG.warning('"{}" does not have the same component count as "{}"!'.format(target, original))
                continue

            target_list.append(target)

        meshMirror(
            original,
            target_list,
            position=position,
            axis=axis,
            search=search,
            replace=replace,
        )

    # mirror deformer pre command
    def applyDeformerMirror(self, original, deformer_str, axis, search, replace):
        if not original or not deformer_str:
            return

        handle_list = [
            handle.strip()
            for handle in deformer_str.split(',')
        ]
        deformerMirror(
            original,
            handle_list,
            axis=axis,
            search=search,
            replace=replace,
        )

    def applyMirror(self):
        mode = mc.radioButtonGrp('ld_mirrorMode_rBGrp', q=True, sl=True)
        axis = mc.radioButtonGrp('ld_mirrorAxis_rBGrp', q=True, sl=True)
        search = mc.textField('ld_mm_search_tField', q=True, tx=True)
        replace = mc.textField('ld_mm_replace_tField', q=True, tx=True)

        cmd_kwargs = {
            'axis': axis,
            'search': search,
            'replace': replace,
        }

        if mode == self.MODE_SHAPE:
            self.applyShapeMirror(
                mc.textField('ld_mCurve_original_tField', q=True, tx=True),
                position=mc.radioButtonGrp('ld_mCurve_position_rBGrp', q=True, sl=True),
                **cmd_kwargs
            )

        elif mode == self.MODE_MESH:
            self.applyMeshMirror(
                mc.textField('ld_mMesh_original_tField', q=True, tx=True),
                mc.textField('ld_mMesh_target_tField', q=True, tx=True),
                position=mc.radioButtonGrp('ld_mMesh_position_rBGrp', q=True, sl=True),
                **cmd_kwargs
            )

        elif mode == self.MODE_DEFORMER:
            self.applyDeformerMirror(
                mc.textField('ld_mDeformer_object_tField', q=True, tx=True),
                mc.textField('ld_mDeformer_deformer_tField', q=True, tx=True),
                **cmd_kwargs
            )

    # --------------------------------------------------------------------------
    def close(self):
        if mc.window(self.win_name, ex=True):
            mc.deleteUI(self.win_name)

    def show(self):
        if mc.window(self.win_name, ex=True):
            mc.showWindow(self.win_name)

    # --------------------------------------------------------------------------
    def setupUi(self):
        mc.window(self.win_name, t='ld_mirrorMe', s=0)
        mc.columnLayout(adj=True)
        mc.frameLayout(label='MirrorMe', cll=0)
        mc.rowColumnLayout(nc=2, adj=2)
        mc.text(label=' Mode:')
        mc.radioButtonGrp(
            'ld_mirrorMode_rBGrp',
            label='',
            la3=['Curve', 'Mesh', 'Deformer'],
            nrb=3,
            cw4=[50, 60, 60, 60],
            cal=[1, 'left'],
            sl=1,
            cc=lambda *_: self.switchMode(),
        )
        mc.text(label=' Axis:')
        mc.radioButtonGrp(
            'ld_mirrorAxis_rBGrp',
            label='',
            la3=['X', 'Y', 'Z'],
            nrb=3,
            cw4=[50, 30, 30, 30],
            cal=[1, 'left'],
            sl=1,
        )
        mc.checkBox(
            'ld_mirrorAxis_negative_cBox',
            label='+/-',
            w=15,
            value=True,
            onc=lambda *_: mc.radioButtonGrp('ld_mirrorAxis_rBGrp', e=True, la3=['X', 'Y', 'Z']),
            ofc=lambda *_: mc.radioButtonGrp('ld_mirrorAxis_rBGrp', e=True, la3=['-X', '-Y', '-Z']),
        )
        mc.setParent('..')
        mc.rowColumnLayout(nc=2, cw=[1, 50], adj=2)
        mc.text(label=' Search:')
        mc.textField('ld_mm_search_tField', tx='L_')
        mc.text(label=' Replace:')
        mc.textField('ld_mm_replace_tField', tx='R_')
        mc.setParent('..')

        # Curve Layout
        mc.frameLayout(
            'ld_mMode1_fLayout',
            l='Curve',
            cll=0,
        )
        mc.radioButtonGrp(
            'ld_mCurve_position_rBGrp',
            label=' Position:',
            la3=['World 0', 'Original', 'Mirrored'],
            nrb=3,
            cw4=[50, 60, 60, 60],
            cal=[1, 'left'],
            sl=1,
        )
        mc.rowLayout(nc=2, adj=1)
        mc.colorIndexSliderGrp(
            'ld_mCurve_colour_cISGrp',
            label=' Colour:',
            cal=[1, 'center'],
            h=20,
            cw3=[35, 30, 90],
            min=1,
            max=32,
            v=7,
        )
        mc.checkBox(
            'ld_mCurve_colour_cBox',
            label='',
            w=15,
            value=True,
            onc=lambda *_: mc.colorIndexSliderGrp('ld_mCurve_colour_cISGrp', e=True, en=True),
            ofc=lambda *_: mc.colorIndexSliderGrp('ld_mCurve_colour_cISGrp', e=True, en=False),
        )
        mc.setParent('..')
        mc.rowColumnLayout(nc=2, cw=[1, 70], adj=2)
        mc.button(
            label='Curve(s)',
            c=lambda *_: self.addToField('ld_mCurve_original_tField', True),
        )
        mc.textField('ld_mCurve_original_tField')
        mc.setParent('..')
        mc.setParent('..')

        # Mesh Layout
        mc.frameLayout('ld_mMode2_fLayout', label='Mesh', cll=0, m=0)
        mc.radioButtonGrp(
            'ld_mMesh_position_rBGrp',
            label=' Position:',
            la2=['Target', 'Original'],
            nrb=2,
            cw3=[50, 90, 90],
            cal=[1, 'left'],
            sl=1,
        )
        mc.rowColumnLayout(nc=2, cw=[1, 70], adj=2)
        mc.button(
            label='Original',
            c=lambda *_: self.addToField('ld_mMesh_original_tField', False),
        )
        mc.textField('ld_mMesh_original_tField')
        mc.button(
            label='Target(s)',
            c=lambda *_: self.addToField('ld_mMesh_target_tField', True),
        )
        mc.textField('ld_mMesh_target_tField')
        mc.setParent('..')
        mc.setParent('..')

        # Deformer Layout
        mc.frameLayout(
            'ld_mMode3_fLayout',
            label='Deformer',
            cll=0,
            m=0,
        )
        mc.text(label='This version only supports Clusters')
        mc.rowColumnLayout(nc=2, cw=[1, 70], adj=2)
        mc.button(
            label='Object',
            c=lambda *_: self.addToField('ld_mDeformer_object_tField', False),
        )
        mc.textField('ld_mDeformer_object_tField')
        mc.button(
            label='Deformer(s)',
            c=lambda *_: self.addToField('ld_mDeformer_deformer_tField', True),
        )
        mc.textField('ld_mDeformer_deformer_tField')
        mc.setParent('..')
        mc.setParent('..')
        mc.button(
            label='Mirror!',
            h=35,
            c=lambda *_: self.applyMirror(),
        )
        mc.setParent('..')


# ------------------------------------------------------------------------------
def launch():
    ui = LDMirrorMeUi()
    return ui


def main():
    return launch()


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
