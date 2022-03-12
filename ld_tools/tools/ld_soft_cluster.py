"""
Quickly create cluster from current soft-selection to speed up workflow.

# Thanks to Brian Escribano's softSelection() script to gather information.

Usage:

    .. code-block:: python

        >>> from ld_tools.tools import ld_soft_cluster
        >>> ld_soft_cluster.create_soft_cluster()

"""
import maya.cmds as mc
import maya.OpenMaya as om


__author__ = 'Lee Dunham'
__version__ = '0.1.1'


# ------------------------------------------------------------------------------
def _get_soft_selection():
    """
    Return the current soft selection components and normalised influence weights.

    :return: List of components and matching weights.
    :rtype: list(str), list(float)
    """
    # Grab the soft selection
    selection = om.MSelectionList()
    soft_sel = om.MRichSelection()
    om.MGlobal.getRichSelection(soft_sel)
    soft_sel.getSelection(selection)
    dag_path = om.MDagPath()
    component = om.MObject()

    # Filter Defeats the purpose of the else statement
    iter_sel = om.MItSelectionList(selection, om.MFn.kMeshVertComponent)
    elements, weights = [], []
    while not iter_sel.isDone():
        iter_sel.getDagPath(dag_path, component)

        # Grab the parent of the shape node
        dag_path.pop()
        node = dag_path.fullPathName()
        fn_comp = om.MFnSingleIndexedComponent(component)
        vtx_str = node + '.vtx[{}]'

        for i in range(fn_comp.elementCount()):
            elements.append(vtx_str.format(fn_comp.element(i)))
            weights.append(fn_comp.weight(i).influence() if fn_comp.hasWeights() else 1.0)

        iter_sel.next()

    return elements, weights


def _reposition_cluster_deformer(cluster, position):
    """
    Reposition the cluster handle using the given position.

    :param cluster: Cluster handle to use.
    :type cluster: str
    :param position: Position to use.
    :type position: list(float, float, float)
    """
    mc.xform(cluster, a=True, ws=True, piv=(position[0], position[1], position[2]))
    deformer = mc.listRelatives(cluster, shapes=True)[0]
    mc.setAttr(deformer + '.origin', position[0], position[1], position[2])


# ------------------------------------------------------------------------------
def create_soft_cluster():
    """
    Create a Cluster deformer using the current soft selection.

    :return: New cluster deformer.
    :rtype: str
    """
    elements, weights = _get_soft_selection()

    # Get the average position from the move manipulator
    mc.setToolTo('Move')
    current_mode = mc.manipMoveContext('Move', q=True, m=True)
    mc.manipMoveContext('Move', e=True, m=0)
    position = mc.manipMoveContext('Move', q=True, p=True)
    mc.manipMoveContext('Move', e=True, m=current_mode)

    obj = mc.listRelatives(mc.listRelatives(parent=True), parent=True)
    new_cluster = mc.cluster(elements, n=obj[0] + '_softCluster')
    for i in range(len(elements)):
        mc.percent(new_cluster[0], elements[i], v=weights[i])

    _reposition_cluster_deformer(new_cluster[1], position)
    return new_cluster[1]


def main():
    create_soft_cluster()


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
