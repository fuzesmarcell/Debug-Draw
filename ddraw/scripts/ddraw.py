import json, os, logging

from maya import cmds
from maya import mel
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin
from maya.api import OpenMaya as om2

from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *

from shiboken2 import wrapInstance
from maya import OpenMayaUI as omui

from functools import  partial

# Global variables
# NOTE(fuzes): For now these are going to be global
_DATA_PATH = "w:/maya/plugins/debugdraw/data/ddrawData.json"

# Global public variables
DDRAW_WINDOW_NAME = "ddraw_window"

#
# I/O related code
#

def saveData(path, data):
    """
    Save data as json file
    :param path: [string] path where to save data
    :param data: [strings]|[integers]|[floats]|[Booleans]|[lists]|[dictionaries]|[None]
    :return: [None]
    """
    f = open(path, "w")
    f.write(json.dumps(data))
    f.close()

def loadData(path):
    """
    Load json data from file path
    :param path: [string] path to the json file
    :return: Returns the json file contents.
    """
    if os.path.isfile(path):

        with open(path, "r") as file:
            data = json.loads(file.read())
            file.close()
            return data
    else:
        raise Exception("The file " + path + "does not exist.")

#
# General utility functions
#

_XBMLANGPATHS = [p for p in os.getenv("XBMLANGPATH").split(";") if os.path.exists(p)]
def getImagePath(name):
    """
    Searches all the image paths in the Maya environment matching to the given [string] parameter.
    If we find a path we return the full path to it. The first item which matches the name will be returned.
    :param name: [string] name of the image to search
    :return: [string] If found returns the a valid path to the found icon. If not returns [None]
    """
    Result = None
    for path in _XBMLANGPATHS:
        for icon in os.listdir(path):
            rawIconName = icon.split(".")[0]
            if rawIconName == name:
                Result = os.path.join(path, icon)

    return Result

#
# Open Maya utility functions
#

def iterSelection():
    """
    generator style iterator over current Maya active selection
    :return: [MObject] an MObject for each item in the selection
    """
    sel = om2.MGlobal.getActiveSelectionList()
    for i in xrange(sel.length()):
        yield sel.getDependNode(i)

_MAYA_MATRIX_ATTRIBUTE_NAME = 'worldMatrix'
# noinspection PyArgumentList
def wMtxPlugFromMob(node_mob):
    """
    finds the world matrix attribute and returns the [MPlug]
    :param node_mob: [MObject] the node to get the world matrix from
    :return: [MPlug] the matrix value of the world transform on the argument node
    """
    if not node_mob.hasFn(om2.MFn.kDagNode):
        return None

    mfn_dag = om2.MFnDagNode(node_mob)
    wMtxPlug = mfn_dag.findPlug(_MAYA_MATRIX_ATTRIBUTE_NAME, False)
    elPlug = wMtxPlug.elementByLogicalIndex(0)

    return elPlug

def getMobFromName(name):
    """
    Find the given [MObject] from the given name in the Maya scene
    :param name: [string] Name of the object
    :return: [MObject]
    """
    selList = om2.MSelectionList()
    selList.add(name)
    mob = selList.getDependNode(0)
    return mob

# noinspection PyArgumentList
def getStringTypeFromMob(mob):
    """
    Retrieves the Maya string type from the given [MObject]
    :param mob: [MObject]
    :return: [string]
    """
    mfn_dep = om2.MFnDependencyNode(mob)
    return cmds.objectType(mfn_dep.name())

def createNodeAndReturnMob(nodeType):
    """
    Creates the given node type and returns the associated [MObject]
    :param nodeType: [string] Maya node type
    :return: [MObject]
    """
    drawNode = cmds.createNode(nodeType)
    return getMobFromName(drawNode)

# noinspection PyArgumentList
def isMatrixPlug(plug):
    """
    Checks whether the given [MPlug] is a matrix plug or not
    :param plug: [MPlug] to be checked
    :return: [bool]
    """
    Result = False
    mob = plug.attribute()
    if mob.apiType() == om2.MFn.kMatrixAttribute:
        Result = True

    if mob.apiType() == om2.MFn.kTypedAttribute:
        mfn_typed = om2.MFnTypedAttribute(mob)
        Result = mfn_typed.attrType() == om2.MFnData.kMatrix

    return Result

# noinspection PyArgumentList
def setFloat3Plug(plug, f3):
    """
    Convenience function to set a Maya MFloatVector plug.

    :param plug: [MPlug] the plug which has 3 children and accepts float values. We are not checking if this is valid!
    :param f3: [iterable] Any object which has the get method []
    :return: [None]
    """
    assert len(f3) > 3

    if plug.isCompound:
        data = plug.asMDataHandle()
        vector = om2.MFloatVector(f3[0], f3[1], f3[2])
        data.setMFloatVector(vector)
        plug.setMDataHandle(data)

def isPointPlug(plug):
    """
    Checks whether the given [MPlug] is a compound and has 3 children
    :param plug: [MPlug]
    :return: [bool]
    """
    IsCompound = plug.isCompound
    if IsCompound:
        return plug.numChildren() == 3

    return False

# noinspection PyArgumentList
def isMobType(mob, objType):
    """
    Check if the given [MObject] is the equal to the Maya string type.
    Not to be confused with the MObject.apiString() method.
    :param mob: [MObject] to check with the given type
    :param objType: [string] Maya object type
    :return: [bool] Whether the [MObject] matches the given [string] type.
    """
    mfn_dep = om2.MFnDependencyNode(mob)
    return cmds.objectType(mfn_dep.name(), isType=objType)

# noinspection PyArgumentList
def convertQColorToMColor(c):
    """
    Utility function to convert from a [QColor] to a [MColor]
    :param c: [QColor]
    :return: [MColor]
    """
    return om2.MColor([c.red() / 255.0, c.green() / 255.0, c.blue() / 255.0])

def convertMColorToQColor(c):
    """
    Simple utility function to convert from a MColor to a QColor
    :param c: [MColor]
    :return: [QColor]
    """
    return QColor(int(c[0]*255), int(c[1]*255), int(c[2]*255))

#
# DDraw functions/classes for drawing in the viewport
#

# noinspection PyArgumentList
def getMatrixAttributesFromMob(mob):
    """
    Given a dependency node returns all the Matrix [MPlug] in a list.
    :param mob: [MObject] The node on which to search all the attributes
    :return: [list] of [MPlug's] which are all matrices
    """
    mfn_dep = om2.MFnDependencyNode(mob)
    attrs = []
    for attr in cmds.listAttr(mfn_dep.name()):
        try:
            plug = mfn_dep.findPlug(attr, False)
        except:
            continue
        if isMatrixPlug(plug):
            attrs.append(plug)
    return attrs

# noinspection PyArgumentList
def getVectorAttributesFromMob(mob):
    """
    Given a dependency node returns all the Point [MPlug] in a list. See the isPointPlug() functions for which is a valid point
    :param mob: [MObject] The node on which to search all the attributes
    :return: [list] of [MPlug's] which are all points
    """
    mfn_dep = om2.MFnDependencyNode(mob)
    attrs = []
    for attr in cmds.listAttr(mfn_dep.name()):
        try:
            plug = mfn_dep.findPlug(attr, False)
        except:
            continue
        if isPointPlug(plug):
            attrs.append(plug)
    return attrs

# noinspection PyClassHasNoInit
class DDrawTypes:
    """
    Enumeration of the all the types.
    """
    kVector = 0
    kMatrix = 1
    kAngle = 2
    kGroup = 3

class DDrawVectorOptions(object):

    # noinspection PyArgumentList,PyArgumentList
    def __init__(self):
        """
        Contains all the options for drawing a DDrawVector.

        [MColor] vectorColor: The color of the vector
        [float] coneRadius: The radius of the cone
        [float] coneHeight: The height of the cone
        [bool] displayText: Should the information text be shown
        [MColor] textColor: The color of the information text
        """

        self.vectorColor = om2.MColor([0, 0, 1, 1])

        self.coneRadius = 0.1
        self.coneHeight = 0.2

        self.displayText = False
        self.textColor = om2.MColor([1, 1, 1, 1])

# noinspection PyArgumentList
def createDDrawNode(name):
    """
    Makes sure that the node editor does not get spammed with our nodes when we create them.
    Also hide the transform node in the outliner so that also does not get spammed with our debug items.
    This function might change depending on what else would be necessary do before/after creating our nodes.

    :param name: [string] Name of the node which should be created. This must be a valid ddraw_node
    :return: [MObject]
    """
    # NOTE(fuzes): Currently we are the only ones calling this so we should never have errors with this!!!
    Result = om2.MObject()
    if name.startswith("ddraw"):

        # NOTE(fuzes): We set the node editor to be not adding on create so we do not clutter it
        # we then after the fact restore it to the previous state
        currentNodeEditor = mel.eval('getCurrentNodeEditor')
        prevState = cmds.nodeEditor(currentNodeEditor, q=True, ann=True)
        cmds.nodeEditor(currentNodeEditor, e=True, ann=False)
        Result = createNodeAndReturnMob(name)
        cmds.nodeEditor(currentNodeEditor, e=True, ann=prevState)
        if Result.hasFn(om2.MFn.kDagNode):
            mfn_dag = om2.MFnDagNode(Result)
            mobParent = mfn_dag.parent(0)
            mfn_dag.setObject(mobParent)
            plug = mfn_dag.findPlug("hiddenInOutliner", False)
            plug.setBool(True)

    return Result

# noinspection PyArgumentList
def getVectorOptionsFromMob(mob):
    """
    Retrieves all the option parameters from a ddraw_vector node.

    :param mob: [MObject] node which corresponds to a ddraw_vector node in the Maya scene
    :return: [DDrawVectorOptions]
    """
    Result = DDrawVectorOptions()

    mfn_dep = om2.MFnDependencyNode(mob)

    vColorPlug = mfn_dep.findPlug("vectorColor", False)
    colorData = vColorPlug.asMDataHandle()
    Result.vectorColor = om2.MColor(colorData.asFloat3())

    coneRadiusPlug = mfn_dep.findPlug("coneRadius", False)
    Result.coneRadius = coneRadiusPlug.asFloat()

    coneHeightPlug = mfn_dep.findPlug("coneHeight", False)
    Result.coneHeight = coneHeightPlug.asFloat()

    displayTextPlug = mfn_dep.findPlug("displayText", False)
    Result.displayText = displayTextPlug.asBool()

    textColorPlug = mfn_dep.findPlug("textColor", False)
    textData = textColorPlug.asMDataHandle()
    Result.textColor = om2.MColor(textData.asFloat3())

    return Result

def setVectorAttributesFromOptions(mob, options = DDrawVectorOptions()):
    """
    Sets the given [MObject] which should be a ddraw_vector node with the given [DDrawVectorOptions]
    :param mob: [MObject] must be a ddraw_vector node
    :param options: [DDrawVectorOptions] from which to fetch the values for settings the attributes on the node
    :return: [None]
    """
    mfn_dep = om2.MFnDependencyNode(mob)

    vColorPlug = mfn_dep.findPlug("vectorColor", False)
    setFloat3Plug(vColorPlug, options.vectorColor)

    coneRadiusPlug = mfn_dep.findPlug("coneRadius", False)
    coneRadiusPlug.setFloat(options.coneRadius)

    coneHeightPlug = mfn_dep.findPlug("coneHeight", False)
    coneHeightPlug.setFloat(options.coneHeight)

    displayTextPlug = mfn_dep.findPlug("displayText", False)
    displayTextPlug.setBool(options.displayText)

    textColorPlug = mfn_dep.findPlug("textColor", False)
    setFloat3Plug(textColorPlug, options.textColor)

# noinspection PyArgumentList
def DDrawVector(plug1, plug2 = om2.MPlug(), drawOptions = DDrawVectorOptions()):
    """
    Creates a ddraw_vector node in the scene. Connects the plug1 to the endPoint attribute
    and the plug2 if available to the origin attribute.
    Rest of the attributes are set to the drawOptions
    :param plug1: [MPlug] which gets connected as the endPoint in the node
    :param plug2: [MPlug] which gets connected as the origin in the node
    :param drawOptions: [DDrawVectorOptions] which specify the settings for the vector to be drawn
    :return: [None
    """
    if not isPointPlug(plug1):
        cmds.error("Invalid plug")

    mob = createDDrawNode("ddraw_vector")

    setVectorAttributesFromOptions(mob, drawOptions)

    mfn_dep = om2.MFnDependencyNode(mob)

    vectorPlug = mfn_dep.findPlug("endPoint", False)
    originPlug = mfn_dep.findPlug("origin", False)
    dgMod = om2.MDGModifier()

    dgMod.connect(plug1, vectorPlug)
    if not plug2.isNull and not isPointPlug(plug2):
        dgMod.connect(plug2, originPlug)

    dgMod.doIt()

class DDrawAngleOptions(object):

    # noinspection PyArgumentList
    def __init__(self):
        """
        Contains all the options from a ddraw_angle node.

        [bool] normalize: Whether the two vectors should be normalized or not
        [MColor] textColor: The color of the text to be displayed
        """
        self.normalize = False
        self.textColor = om2.MColor([1, 1, 1, 1])

def getAngleOptionsFromMob(mob):
    """
    Retrieves the the option attributes from the given ddraw_angle node

    :param mob: [MObject] which must be a ddraw_node from which to retrieve the options
    :return: [DDrawAngleOptions] filled up from the [MObject] attributes
    """
    Result = DDrawAngleOptions()

    mfn_dep = om2.MFnDependencyNode(mob)
    displayPlug = mfn_dep.findPlug("normalize", False)
    Result.normalize = displayPlug.asBool()

    textColorPlug = mfn_dep.findPlug("textColor", False)
    textData = textColorPlug.asMDataHandle()
    Result.textColor = om2.MColor(textData.asFloat3())

    return Result

def setAngleAttributesFromOptions(mob, options = DDrawAngleOptions()):
    """
    Sets all the attributes on a ddraw_angle node given the options

    :param mob: [MObject] which must be a ddraw_angle node on which to set it's attributes
    :param options: [DDrawAngleOptions] containing the options
    :return: [None]
    """

    mfn_dep = om2.MFnDependencyNode(mob)

    normalizePlug = mfn_dep.findPlug("normalize", False)
    normalizePlug.setBool(options.normalize)

    textColorPlug = mfn_dep.findPlug("textColor", False)
    setFloat3Plug(textColorPlug, options.textColor)

# noinspection PyArgumentList
def DDrawAngle(plug1, plug2, options = DDrawAngleOptions()):
    """
    Creates a ddraw_angle node in the Maya scene and connects the plug1, plug2 into the v1 and v2 attributes
    of the node. Additional options can be passed for the angle node

    :param plug1: [MPlug] for the first vector (v1)
    :param plug2: [MPlug] for the second vector (v2)
    :param options: [DDrawAngleOptions] defining the information's in the viewport
    :return: [None]
    """

    if not isPointPlug(plug1) and not isPointPlug(plug2):
        cmds.error("Invalid plug")

    mob = createDDrawNode("ddraw_angle")
    setAngleAttributesFromOptions(mob, options)

    mfn_dep = om2.MFnDependencyNode(mob)
    angle1Plug = mfn_dep.findPlug("vector1", False)
    angle2Plug = mfn_dep.findPlug("vector2", False)

    dagMod = om2.MDagModifier()
    dagMod.connect(plug1, angle1Plug)
    dagMod.connect(plug2, angle2Plug)

    dagMod.doIt()

class DDrawMatrixOptions(object):

    # noinspection PyArgumentList
    def __init__(self):
        """
        Contains all the parameter options for a ddraw_matrix node.

        [bool] displayText: Whether the text should be displayed or not
        [MColor] textColor: The color of the text
        """
        self.displayText = False
        self.textColor = om2.MColor([1, 1, 1, 1])

def getMatrixOptionsFromMob(mob):
    """
    Retrieves the options from the given [MObject] which must be a ddraw_matrix node.

    :param mob: [MObject] from which to get the options
    :return: [DDrawMatrixOptions]
    """
    Result = DDrawMatrixOptions()

    mfn_dep = om2.MFnDependencyNode(mob)
    displayPlug = mfn_dep.findPlug("displayText", False)
    Result.displayText = displayPlug.asBool()

    textColorPlug = mfn_dep.findPlug("textColor", False)
    textData = textColorPlug.asMDataHandle()
    Result.textColor = om2.MColor(textData.asFloat3())

    return Result

def setMatrixOptionsFromMob(mob, options = DDrawMatrixOptions()):
    """
    Set the attributes on the [MObject] from the given options.

    :param mob: [MObject] ddraw_matrix node on which to set the attributes
    :param options: [DDrawMatrixOptions] the options used for setting the attributes
    :return: [None]
    """
    mfn_dep = om2.MFnDependencyNode(mob)

    displayPlug = mfn_dep.findPlug("displayText", False)
    displayPlug.setBool(options.displayText)

    textColorPlug = mfn_dep.findPlug("textColor", False)
    setFloat3Plug(textColorPlug, options.textColor)

# noinspection PyArgumentList
def DDrawMatrix(plug, options = DDrawMatrixOptions()):
    """
    Creates a ddraw_matrix node in the Maya scene and connects the plug to the inMatrix attribute of the node.
    Additional options can be specified.

    :param plug: [MPlug] which gets connected to the inMatrix attribute
    :param options: [DDrawMatrixOptions] specifying what should be displayed in the viewport
    :return: [None]
    """
    if not isMatrixPlug(plug):
        cmds.error("Invalid plug. Can not perform DDrawMatrix")

    mob = createDDrawNode("ddraw_matrix")

    setMatrixOptionsFromMob(mob, options)

    mfn_dep = om2.MFnDependencyNode(mob)

    inMatrixPlug = mfn_dep.findPlug("inMatrix", False)
    dagMod = om2.MDGModifier()
    dagMod.connect(plug, inMatrixPlug)
    dagMod.doIt()

# noinspection PyArgumentList
def DrawVector(options = DDrawVectorOptions(), *args):
    """
    Draws a vector in the viewport with the given options.
    Uses the selection and default attributes to determine which plugs should be connected to the ddraw_vector node.

    :param options: [DDrawVectorOptions]
    :param args: [*args] reserved mostly for the Maya UI which calls this function
    :return: [None]
    """
    for mob in iterSelection():
        # HACK(fuzes): Remove this we are now just testing this we should make this way more procedural then this
        for k, i in loadData(_DATA_PATH)["vector"].iteritems():
            if isMobType(mob, k):
                mfn_dep = om2.MFnDependencyNode(mob)
                DDrawVector(mfn_dep.findPlug(i, False), drawOptions=options)

# noinspection PyArgumentList,PyArgumentList
def DrawAngle(options = DDrawAngleOptions(), *args):
    """
    Draws a angle in the viewport with the given options.
    Uses the selection and default attribute to determine which plugs should be connected to the ddraw_angle node.

    :param options: [DDrawAngleOptions]
    :param args: [*args] reserved mostly for the Maya UI which calls this function
    :return: [None]
    """
    sel = list(iterSelection())
    if len(sel) != 2:
        cmds.warning("Selection must be two nodes!")
        return
    mob1 = sel[0]
    mob2 = sel[1]
    plug1 = None
    plug2 = None

    for k, i in loadData(_DATA_PATH)["vector"].iteritems():
        if isMobType(mob1, k):
            mfn_dep = om2.MFnDependencyNode(mob1)
            plug1 = mfn_dep.findPlug(i, False)

    for k, i in loadData(_DATA_PATH)["vector"].iteritems():
        if isMobType(mob2, k):
            mfn_dep = om2.MFnDependencyNode(mob2)
            plug2 = mfn_dep.findPlug(i, False)

    DDrawAngle(plug1, plug2, options)

def getDDrawAngleOptionFromQSettings():
    """
    Retrieves the options for a ddraw_angle node from the QSettings. If there are None available,
    the default attribute types will be set.

    :return: [DDrawAngleOption] with the all the option parameters used from QSettings
    """
    Result = DDrawAngleOptions()

    settings = QSettings("fuzes", "ddraw")
    if settings.value("angleNormalize"):
        Result.normalize = settings.value("angleNormalize") == u'true'
    if settings.value("angleTextColor"):
        Result.textColor = convertQColorToMColor(settings.value("angleTextColor"))

    return Result

def DrawAngleFromQSettings(*args):
    """
    Convenience function which draws a angle from the QSetttings
    :param args:
    :return:
    """
    DrawAngle(getDDrawAngleOptionFromQSettings())

def DrawVectorFromQSettings(*args):
    """
    Convenience function which draws a vector from the QSettings
    :return: [None]
    """
    DrawVector(getDDrawVectorOptionFromQSettings())

def getDDrawVectorOptionFromQSettings():
    """
    Fetches all the options from the QSettings and returns a new [DDrawVectorOption] from the settings.
    If no settings are found the values are set to the default settings from DDrawVectorOption
    :return: [DDrawVectorOptions] filled up with all the settings
    """

    Result = DDrawVectorOptions()

    settings = QSettings("fuzes", "ddraw")
    if settings.value("vectorColor"):
        Result.vectorColor = convertQColorToMColor(settings.value("vectorColor"))
    if settings.value("coneRadius"):
        Result.coneRadius = float(settings.value("coneRadius"))
    if settings.value("coneHeight"):
        Result.coneHeight = float(settings.value("coneHeight"))
    if settings.value("displayText"):
        Result.displayText = settings.value("displayText") == u'true'
    if settings.value("textColor"):
        Result.textColor = convertQColorToMColor(settings.value("textColor"))

    return Result

# noinspection PyArgumentList
def DrawMatrix(options = DDrawMatrixOptions(), *args):
    """
        Draws a matrix in the viewport with the given options.
        Uses the selection and default attribute to determine which plugs should be connected to the ddraw_matrix node.

        :param options: [DDrawMatrixOptions]
        :param args: [*args] reserved mostly for the Maya UI which calls this function
        :return: [None]
        """
    for mob in iterSelection():
        for k, i in loadData(_DATA_PATH)["matrix"].iteritems():
            if isMobType(mob, k):
                mfn_dep = om2.MFnDependencyNode(mob)
                DDrawMatrix(mfn_dep.findPlug(i, False), options = options)

def getDDrawMatrixOptionFromQSettings():
    """
        Retrieves the options for a ddraw_matrix node from the QSettings. If there are None available,
        the default attribute types will be set.

        :return: [DDrawMatrixOption] with the all the option parameters used from QSettings
    """
    Result = DDrawMatrixOptions()

    settings = QSettings("fuzes", "ddraw")
    if settings.value("matrixDisplayText"):
        Result.displayText = settings.value("matrixDisplayText") == u'true'
    if settings.value("matrixTextColor"):
        Result.textColor = convertQColorToMColor(settings.value("matrixTextColor"))
    return Result

def DrawMatrixFromQSettings(*args):
    """
    Convenience function which draws a matrix from the QSettings
    :return: [None]
    """
    DrawMatrix(getDDrawMatrixOptionFromQSettings())

#
# UI related code
#

class DDrawAttribute(MayaQWidgetBaseMixin, QDialog):
    # noinspection PyArgumentList
    def __init__(self, mob, mode, parent=None):
        """
        Creates a UI which list's all the available attributes which can be drawn from the given node.

        :param mode: [DDrawDrawables] type of enumeration
        :param mob: [MObject] from which to list all the attributes
        :param parent: [Q*] any Q*
        """
        super(DDrawAttribute, self).__init__(parent=parent)

        self.mode = mode
        self.mobHandle = om2.MObjectHandle(mob)

        self.setWindowIcon(QIcon("W:/maya/plugins/debugdraw/data/design.svg"))
        self.setWindowTitle("Save default attribute")

        self.txt = QLineEdit()
        self.txt.setMinimumHeight(26)
        self.txt.setPlaceholderText("Filter:")
        self.txt.textChanged.connect(self._on_filter_text_changed)

        self.view = QListView()
        plugList = []
        if mode == DDrawTypes.kVector:
            plugList = getVectorAttributesFromMob(mob)
        elif mode == DDrawTypes.kMatrix:
            plugList = getMatrixAttributesFromMob(mob)

        model = DDrawPlugListModel(plugList)

        self.sortModel = QSortFilterProxyModel()
        self.sortModel.setSourceModel(model)
        self.view.setModel(self.sortModel)

        btn = QPushButton("Save as Default")
        btn.setIcon(QIcon("W:/maya/plugins/debugdraw/data/floppy-disk.svg"))
        btn.clicked.connect(self._run_save_as_default)

        lyt = QVBoxLayout()
        lyt.addWidget(self.txt)
        lyt.addWidget(self.view)
        lyt.addWidget(btn)

        self.setLayout(lyt)

    def _on_filter_text_changed(self):
        self.sortModel.setFilterFixedString(self.txt.text())

    def _run_save_as_default(self):
        index = self.view.currentIndex()
        plugData = index.data(Qt.UserRole)
        data = loadData(_DATA_PATH)
        mob = list(iterSelection())[0]
        # TODO(fuzes): Check if the key already exists in the dictionary
        if self.mode == DDrawTypes.kMatrix:
            data["matrix"][getStringTypeFromMob(mob)] = plugData.partialName(useLongNames = False)
        elif self.mode == DDrawTypes.kVector:
            data["vector"][getStringTypeFromMob(mob)] = plugData.partialName(useLongNames = False)
        saveData(_DATA_PATH, data)
        self.close()

# noinspection PyMethodOverriding,PyMethodOverriding
class DDrawPlugListModel(QAbstractListModel):
    def __init__(self, data, parent=None, *args):
        """
        A basic implementation of the QAbstractListModel to show all the available plugs.

        :param data: [list] containing [MPlug]'s
        :param parent: [Q*]
        :param args:
        """
        QAbstractListModel.__init__(self, parent, *args)
        self.listdata = data

    def rowCount(self, parent=QModelIndex()):
        return len(self.listdata)

    def data(self, index, role):

        if not index.isValid():
            return

        if  role == Qt.DisplayRole:
            return self.listdata[index.row()].name().split(".")[-1]
        if role == Qt.UserRole:
            return self.listdata[index.row()]

def initMarkingMenu(menuName):
    """
    Initialize a Maya marking menu
    :param menuName: [string] Name of the marking menu
    :return: [string] the name of the popupMenu created by Maya
    """
    if cmds.popupMenu(menuName, ex=True):
        cmds.deleteUI(menuName)

    menu = cmds.popupMenu(menuName,
                          mm=1,
                          b=2,
                          aob=1,
                          ctl=1,
                          alt=1,
                          sh=0,
                          p="nodeEditorPanel1",
                          pmo=0,
                          )
    return menu

def runSaveDefaultAttributeDialog(mode, *args):
    """
    Creates a dialog window prompting the user to choose from the attribute list.
    The selected attribute will be saved once the Save buttons gets pressed and the drawing
    will automatically choose that attribute to be displayed.
    If no node is selected a warning call gets executed (cmds.warning)
    :param mode: [DDrawDrawables] for know can be either kMatrix or kVector. kAngle is not supported
    :return: [None]
    """
    selection = cmds.ls(sl=True)
    if len(selection) > 0:
        app = DDrawAttribute(getMobFromName(selection[0]), mode)
        app.show()
    else:
        cmds.warning("Nothing selected. Can not display attributes")

# noinspection PyUnresolvedReferences
class ColorPushButton(QPushButton):

    colorChanged = Signal(QColor)

    def __init__(self, color = QColor(255, 255, 255), parent = None):
        """
        Simple [QPushButton] which changes its color depending on what gets chosen from the QColorDialog.
        The QColorDialog is connected to the button clicked event

        Signal slots:
        colorChanged: emitted after the QDialog has been closed with the chosen color

        :param color: [QColor] The default color of the button
        :param parent: [Q*] Any Q*
        """
        super(ColorPushButton, self).__init__(parent = parent)

        self.color = color

        self.setColor(color)
        self.clicked.connect(self._run_color_dialog)

    def setColor(self, color):
        pal = self.palette()
        pal.setColor(QPalette.Button, color)
        self.setAutoFillBackground(True)
        self.setPalette(pal)
        self.update()

    def _run_color_dialog(self):
        color = QColorDialog(self)
        color.exec_()
        selectedColor = color.selectedColor()
        self.setColor(selectedColor)
        self.color = selectedColor
        self.colorChanged.emit(self.color)

# noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
class DDrawVectorParametersWidget(QWidget):

    dataChanged = Signal()
    vectorColorChanged = Signal(QColor)
    coneRadiusChanged = Signal(float)
    coneHeightChanged = Signal(float)
    displayTextToggled = Signal(bool)
    textColorChanged = Signal(QColor)

    def __init__(self, settings = DDrawVectorOptions(), parent = None):
        """
        Creates a QWidget from the [DDrawVectorOptions] options. List all the possible parameters for a
        ddraw_vector node. Allows you to easily change the relevant attributes and receive signals from the changes.

        Signals:
        dataChanged: Signal will be emitted if any of the data changes on the widget
        vectorColorChanged: [QColor] Signal will be emitted when the vectorColor changes
        coneRadiusChanged: [float] Signal will be emitted when the coneRadius changes
        coneHeightChanged: [float] Signal will be emitted when the coneHeight changes
        displayTextToggled: [bool] Signal will be emitted when the displayText checkbox is being toggled
        textColorChanged: [QColor] Signal will be emitted when the vectorColor changes

        :param settings: [DDrawVectorOptions] for the initial values on the attributes on the widget
        :param parent: [Q*]
        """
        super(DDrawVectorParametersWidget, self).__init__(parent = parent)

        self.vectorColorBtn = ColorPushButton(convertMColorToQColor(settings.vectorColor))
        self.vectorColorBtn.colorChanged.connect(self._on_vector_color_changed)

        self.coneRadius = QDoubleSpinBox()
        self.coneRadius.setSingleStep(0.1)
        self.coneRadius.setMinimum(0)
        self.coneRadius.setValue(settings.coneRadius)
        self.coneRadius.valueChanged.connect(self._on_cone_radius_changed)

        self.coneHeight = QDoubleSpinBox()
        self.coneHeight.setSingleStep(0.1)
        self.coneHeight.setMinimum(0)
        self.coneHeight.setValue(settings.coneHeight)
        self.coneHeight.valueChanged.connect(self._on_cone_radius_changed)

        self.displayText = QCheckBox()
        self.displayText.setChecked(settings.displayText)
        self.displayText.toggled.connect(self._on_display_text_toggled)

        self.textColorBtn = ColorPushButton(convertMColorToQColor(settings.textColor))
        self.textColorBtn.colorChanged.connect(self._on_text_color_changed)

        layout = QFormLayout()
        layout.addRow("Vector Color", self.vectorColorBtn)
        layout.addRow("Cone Radius", self.coneRadius)
        layout.addRow("Cone Height", self.coneHeight)
        layout.addRow("Display Text", self.displayText)
        layout.addRow("Text Color", self.textColorBtn)

        self.setLayout(layout)

    def _on_vector_color_changed(self, color):
        self.vectorColorChanged.emit(color)
        self.dataChanged.emit()
    def _on_cone_radius_changed(self, value):
        self.coneRadiusChanged.emit(value)
        self.dataChanged.emit()
    def _on_cone_height_changed(self, value):
        self.coneHeightChanged.emit(value)
        self.dataChanged.emit()
    def _on_display_text_toggled(self, value):
        self.displayTextToggled.emit(value)
        self.dataChanged.emit()
    def _on_text_color_changed(self, color):
        self.textColorChanged.emit(color)
        self.dataChanged.emit()

    def getDrawVectorOptions(self):

        Result = DDrawVectorOptions()

        Result.vectorColor = convertQColorToMColor(self.vectorColorBtn.color)
        Result.textColor = convertQColorToMColor(self.textColorBtn.color)
        Result.coneRadius = self.coneRadius.value()
        Result.coneHeight = self.coneHeight.value()
        Result.displayText = self.displayText.isChecked()

        return Result

class DDrawVectorOptionsWindow(MayaQWidgetBaseMixin, QWidget):

    def __init__(self, parent = None):
        super(DDrawVectorOptionsWindow, self).__init__(parent = parent)

        self.setWindowIcon(QIcon("W:/maya/plugins/debugdraw/data/design.svg"))
        self.setWindowTitle("Draw Vector Options")

        self.vectorWidget = DDrawVectorParametersWidget(getDDrawVectorOptionFromQSettings())

        drawBtn = QPushButton("Draw")
        drawBtn.clicked.connect(self._run_draw_vector)
        closeBtn = QPushButton("Close")
        closeBtn.clicked.connect(self.close)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(drawBtn)
        buttonLayout.addWidget(closeBtn)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.vectorWidget)
        mainLayout.addWidget(line)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)

    def _run_draw_vector(self):
        # NOTE(fuzes): We just fetch all the data from the UI for the command to draw the vector
        options = self.vectorWidget.getDrawVectorOptions()
        DrawVector(options)

        settings = QSettings("fuzes", "ddraw")
        settings.setValue("vectorColor", convertMColorToQColor(options.vectorColor))
        settings.setValue("coneRadius", options.coneRadius)
        settings.setValue("coneHeight", options.coneHeight)
        settings.setValue("displayText", options.displayText)
        settings.setValue("textColor", convertMColorToQColor(options.textColor))

        self.close()

    def showAtCursor(self):
        cursor = self.mapFromGlobal(QCursor.pos())
        width = 300
        height = 100
        self.setGeometry(0,0, width, height)
        t = QPoint(-width/2, -height/2)

        t += cursor

        self.move(t)
        self.show()

# noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
class DDrawMatrixParametersWidget(QWidget):

    dataChanged = Signal()
    displayTextToggled = Signal(bool)
    textColorChanged = Signal(QColor)

    def __init__(self, settings = DDrawMatrixOptions(), parent = None):
        """
        Creates a QWidget from the [DDrawMatrixOptions] options. List all the possible parameters for a
        ddraw_matrix node. Allows you to easily change the relevant attributes and receive signals from the changes.

        Signals:
        dataChanged: Signal will be emitted if any of the data changes on the widget
        displayTextToggled: [bool] Signal will be emitted when the displayText checkbox is being toggled
        textColorChanged: [QColor] Signal will be emitted when the vectorColor changes

        :param settings: [DDrawMatrixOptions] for the initial values on the attributes on the widget
        :param parent: [Q*]
        """
        super(DDrawMatrixParametersWidget, self).__init__(parent = parent)

        self.displayText = QCheckBox()
        self.displayText.setChecked(settings.displayText)
        self.displayText.toggled.connect(self._on_display_text_toggled)

        self.textColorBtn = ColorPushButton(convertMColorToQColor(settings.textColor))
        self.textColorBtn.colorChanged.connect(self._on_text_color_changed)

        mainLayout = QFormLayout()
        mainLayout.addRow("Display Text", self.displayText)
        mainLayout.addRow("Text Color", self.textColorBtn)

        self.setLayout(mainLayout)

    def _on_display_text_toggled(self, value):
        self.displayTextToggled.emit(value)
        self.dataChanged.emit()
    def _on_text_color_changed(self, color):
        self.textColorChanged.emit(color)
        self.dataChanged.emit()

    def getDrawMatrixOptions(self):
        Result = DDrawMatrixOptions()

        Result.textColor = convertQColorToMColor(self.textColorBtn.color)
        Result.displayText = self.displayText.isChecked()

        return Result

class DDrawMatrixOptionsWindow(MayaQWidgetBaseMixin, QWidget):

    def __init__(self, parent = None):
        super(DDrawMatrixOptionsWindow, self).__init__(parent = parent)

        self.setWindowIcon(QIcon("W:/maya/plugins/debugdraw/data/design.svg"))
        self.setWindowTitle("Draw Matrix Options")

        self.matrixWidget = DDrawMatrixParametersWidget()

        drawBtn = QPushButton("Draw")
        drawBtn.clicked.connect(self._run_draw_matrix)
        closeBtn = QPushButton("Close")
        closeBtn.clicked.connect(self.close)

        lyt1 = QHBoxLayout()
        lyt1.addWidget(drawBtn)
        lyt1.addWidget(closeBtn)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.matrixWidget)
        mainLayout.addWidget(line)
        mainLayout.addLayout(lyt1)

        self.setLayout(mainLayout)

    def _run_draw_matrix(self):
        options = self.matrixWidget.getDrawMatrixOptions()

        DrawMatrix(options)

        settings = QSettings("fuzes", "ddraw")
        settings.setValue("matrixDisplayText", options.displayText)
        settings.setValue("matrixTextColor", convertMColorToQColor(options.textColor))

        self.close()

    def showAtCursor(self):
        cursor = self.mapFromGlobal(QCursor.pos())
        width = 300
        height = 100
        self.setGeometry(0,0, width, height)
        t = QPoint(-width/2, -height/2)

        t += cursor

        self.move(t)
        self.show()

# noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
class DDrawAngleParametersWidget(QWidget):

    dataChanged = Signal()
    normalizeToggled = Signal(bool)
    textColorChanged = Signal(QColor)

    def __init__(self, settings = DDrawAngleOptions(), parent = None):
        """
        Creates a QWidget from the [DDrawAngleOptions] options. List all the possible parameters for a
        ddraw_angle node. Allows you to easily change the relevant attributes and receive signals from the changes.

        Signals:
        dataChanged: Signal will be emitted if any of the data changes on the widget
        normalizeToggled: [bool] Signal will be emitted when the normalize checkbox is being toggled
        textColorChanged: [QColor] Signal will be emitted when the vectorColor changes

        :param settings: [DDrawAngleOptions] for the initial values on the attributes on the widget
        :param parent: [Q*]
        """
        super(DDrawAngleParametersWidget, self).__init__(parent = parent)

        self.normalize = QCheckBox()
        self.normalize.setChecked(settings.normalize)
        self.normalize.toggled.connect(self._on_normalize_toggled)

        self.textColorBtn = ColorPushButton(convertMColorToQColor(settings.textColor))
        self.textColorBtn.colorChanged.connect(self._on_text_color_changed)

        mainLayout = QFormLayout()
        mainLayout.addRow("Normalize", self.normalize)
        mainLayout.addRow("Text Color", self.textColorBtn)

        self.setLayout(mainLayout)

    def _on_normalize_toggled(self, value):
        self.normalizeToggled.emit(value)
        self.dataChanged.emit()
    def _on_text_color_changed(self, color):
        self.textColorChanged.emit(color)
        self.dataChanged.emit()

    def getDrawAngleOptions(self):
        Result = DDrawAngleOptions()

        Result.textColor = convertQColorToMColor(self.textColorBtn.color)
        Result.normalize = self.normalize.isChecked()

        return Result

class DDrawAngleOptionsWindow(MayaQWidgetBaseMixin, QWidget):

    def __init__(self, parent = None):
        super(DDrawAngleOptionsWindow, self).__init__(parent = parent)

        self.setWindowIcon(QIcon("W:/maya/plugins/debugdraw/data/design.svg"))
        self.setWindowTitle("Draw Angle Options")

        self.angleWidget = DDrawAngleParametersWidget()

        drawBtn = QPushButton("Draw")
        drawBtn.clicked.connect(self._run_draw_angle)
        closeBtn = QPushButton("Close")
        closeBtn.clicked.connect(self.close)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(drawBtn)
        buttonLayout.addWidget(closeBtn)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.angleWidget)
        mainLayout.addWidget(line)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)

    def _run_draw_angle(self):
        options = self.angleWidget.getDrawAngleOptions()

        DrawAngle(options)

        settings = QSettings("fuzes", "ddraw")
        settings.setValue("angleNormalize", options.normalize)
        settings.setValue("angleTextColor", convertMColorToQColor(options.textColor))

        self.close()

    def showAtCursor(self):
        cursor = self.mapFromGlobal(QCursor.pos())
        width = 300
        height = 100
        self.setGeometry(0,0, width, height)
        t = QPoint(-width/2, -height/2)

        t += cursor

        self.move(t)
        self.show()

def RunVectorOptions(*args):
    app = DDrawVectorOptionsWindow()
    app.showAtCursor()

def RunMatrixOptions(*args):
    app = DDrawMatrixOptionsWindow()
    app.showAtCursor()

def RunAngleOptions(*args):
    app = DDrawAngleOptionsWindow()
    app.showAtCursor()

class BaseTreeItem(object):

    def __init__(self, typeIdentifier, data = None, parent = None):
        """
        A generic implementation of a Tree data structure.
        The main purpose of this class was to make it easier to use with the QAbstractItemModel.
        This is just the same class used in the Qt examples:
        http://doc.qt.io/qt-5/qtwidgets-itemviews-editabletreemodel-treeitem-cpp.html

        :param data: [*] The data which should be stored with the node
        :param parent: [BaseTreeItem] which is the parent of this instance
        """
        self.parent = parent
        self.data = data
        self.type = typeIdentifier
        self.children = []

    def childCount(self):
        return len(self.children)

    def child(self, row):
        return self.children[row]

    def addChild(self, node):
        node.parent = self
        self.children.append(node)

    def removeChildren(self, position, count):

        if position < 0 or position + count > self.childCount():
            return False

        for row in xrange(count):
            del self.children[position]

        return True

    def insertChild(self, position, item):

        if position < 0 or position > self.childCount():
            return False

        self.children.insert(position, item)
        return True

    def insertChildren(self, position, count):

        for x in xrange(count):
            item = BaseTreeItem(-1, parent=self)
            self.insertChild(position, item)

        return True

    def row(self):
        if self.parent:
            return self.parent.children.index(self)

        return 0

# noinspection PyMethodOverriding,PyMethodOverriding,PyMethodOverriding,PyMethodOverriding,PyMethodOverriding,PyMethodOverriding,PyMethodOverriding,PyMethodOverriding,PyMethodOverriding,PyMethodOverriding
class TreeModel(QAbstractItemModel):

    def __init__(self, root):
        """
        Implementation of the QAbstractItemModel for using with the BaseTreeItem model.

        :param root: [BaseTreeItem] the root which will not be visible and acts as a invalid index
        """
        super(TreeModel, self).__init__()
        self.root = root

    def data(self, index, role):

        if not index.isValid():
            return

        item = index.internalPointer()
        data = item.data

        if role == Qt.DisplayRole:
            return data["displayName"]
        elif role == Qt.DecorationRole:
            return data["decoration"]

    def headerData(self, section, orientation, role = Qt.DisplayRole):

        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return "DDraw Outliner"

    def index(self, row, column, parent = QModelIndex()):

        if not QAbstractItemModel.hasIndex(self, row, column, parent):
            return QModelIndex()

        parentItem = self.getItem(parent)

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, 0, childItem)
        else:
            return QModelIndex()

    def parent(self, index):

        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent

        if parentItem == self.root:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent = QModelIndex()):

        parentItem = self.getItem(parent)
        return parentItem.childCount()

    def flags(self, index):

        if not index.isValid():
            return 0

        return Qt.ItemIsEditable | QAbstractItemModel.flags(self, index)

    def columnCount(self, parent = QModelIndex()):
        return 1

    #
    # These functions are here for a TreeView which can be edited
    #

    def setData(self, index, value, role = Qt.EditRole):

        if role != Qt.EditRole:
            return False

        item = self.getItem(index)
        item.data = value[1]
        item.type = value[0]
        self.dataChanged.emit(index, index)

        return True

    def insertRows(self, position, rows, parent = QModelIndex()):

        parentItem = self.getItem(parent)

        self.beginInsertRows(parent, position, position + rows - 1)
        Result = parentItem.insertChildren(position, rows)
        self.endInsertRows()

        return Result

    def removeRows(self, position, rows, parent = QModelIndex()):

        Result = False
        if not parent.isValid():
            return Result

        parentItem = self.getItem(parent)

        self.beginRemoveRows(parent, position, position + rows - 1)
        Result = parentItem.removeChildren(position, rows)
        self.endRemoveRows()

        return Result

    #
    # Utility function to return the item
    #

    def getItem(self, index):

        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self.root

# noinspection PyArgumentList,PyArgumentList
def getDataFromMob(mob):
    """
    Retrieves the relevant data for a [MObject]
    Automatically searches for the icon name from the string type of the object.

    :param mob: [MObject]
    :return: [dict] Filled up with the data. Key[data] = [MObjectHandle], Key[displayName] = Object name,
    Key[decoration] = Path of the icon. If not found will be None
    """

    mfn_dep = om2.MFnDependencyNode(mob)
    iconPath = getImagePath(getStringTypeFromMob(mob))
    return getDataDict(mfn_dep.name(), om2.MObjectHandle(mob), icon=QIcon(iconPath))

def getDataDict(displayName = "", data = None, icon = QIcon(":/group")):
    """
    Utility function for creating a data dictionary for using the the BaseTreeItem

    :param displayName: [string] which gets display by the TreeView
    :param data: [*] any data the user might want to store with the item
    :param icon: [string] path to a valid icon which gets displayed by the TreeView
    :return: [dict]
    """
    return {
        "data":data,
        "displayName":displayName,
        "decoration":icon
    }

def getDDrawTreeRoot():
    """
    Creates a tree data structure with the [BaseTreeItem] object.
    Creates groups for all the ddraw_nodes and finds all the ddraw_nodes and adds the nodes to the
    correct groups so it can be display in the TreeView correctly

    :return: [BaseTreeItem] root item of the tree
    """

    vectorNodes = cmds.ls(type = "ddraw_vector")
    matrixNodes = cmds.ls(type = "ddraw_matrix")
    angleNodes = cmds.ls(type = "ddraw_angle")

    # TODO(fuzes): For now we just pass -1 as the type for the root so we know this is a invalid type to be ignored
    root = BaseTreeItem(-1, getDataDict())

    vector = BaseTreeItem(DDrawTypes.kGroup, getDataDict(displayName="Vectors"))
    root.addChild(vector)
    for name in vectorNodes:
        mob = getMobFromName(name)
        item = BaseTreeItem(DDrawTypes.kVector, getDataFromMob(mob))
        vector.addChild(item)

    matrix = BaseTreeItem(DDrawTypes.kGroup, getDataDict(displayName="Matrices"))
    root.addChild(matrix)
    for name in matrixNodes:
        mob = getMobFromName(name)
        item = BaseTreeItem(DDrawTypes.kMatrix, getDataFromMob(mob))
        matrix.addChild(item)

    angle = BaseTreeItem(DDrawTypes.kGroup,getDataDict(displayName="Angles"))
    root.addChild(angle)
    for name in angleNodes:
        mob = getMobFromName(name)
        item = BaseTreeItem(DDrawTypes.kAngle, getDataFromMob(mob))
        angle.addChild(item)

    return root

# noinspection PyMethodOverriding,PyArgumentList
class DDrawWindow(MayaQWidgetBaseMixin, QWidget):

    callbacks = om2.MCallbackIdArray()
    runSelectionCallback = True

    def __init__(self, parent = None):
        super(DDrawWindow, self).__init__(parent = parent)

        qss = """
        QTreeView{
        font-size: 14px;
        }
        """

        # TODO(fuzes): Size policy
        self.setObjectName(DDRAW_WINDOW_NAME)

        self.replacementWidget = QWidget()

        self.view = QTreeView()
        self.view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.view.setStyleSheet(qss)
        self.view.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))

        self.root = getDDrawTreeRoot()
        self.model = TreeModel(self.root)
        self.view.setModel(self.model)
        self.view.selectionModel().selectionChanged.connect(self._on_tree_view_selection_changed)

        shortcut = QShortcut(QKeySequence(Qt.Key_Delete), self)
        shortcut.activated.connect(self.removeRow)

        self.mainLayout = QHBoxLayout()
        self.mainLayout.addWidget(self.view)
        self.mainLayout.addWidget(self.replacementWidget)

        self.setLayout(self.mainLayout)

        #
        # Maya related stuff starts here
        #

        # NOTE(fuzes): All callbacks related to when we create our nodes
        vectorCallbackID = om2.MDGMessage.addNodeAddedCallback(self._on_ddraw_node_added, "ddraw_vector",
                                                               DDrawTypes.kVector)
        matrixCallbackID = om2.MDGMessage.addNodeAddedCallback(self._on_ddraw_node_added, "ddraw_matrix",
                                                               DDrawTypes.kMatrix)
        angleCallbackID = om2.MDGMessage.addNodeAddedCallback(self._on_ddraw_node_added, "ddraw_angle",
                                                              DDrawTypes.kAngle)
        self.callbacks.append(vectorCallbackID)
        self.callbacks.append(matrixCallbackID)
        self.callbacks.append(angleCallbackID)

        # NOTE(fuzes): When our nodes get deleted callbacks
        vectorNodeRemovedCallbackID = om2.MDGMessage.addNodeRemovedCallback(self.nodeRemovedCallback, "ddraw_vector")
        matrixNodeRemovedCallbackID = om2.MDGMessage.addNodeRemovedCallback(self.nodeRemovedCallback, "ddraw_matrix")
        angleNodeRemovedCallbackID = om2.MDGMessage.addNodeRemovedCallback(self.nodeRemovedCallback, "ddraw_angle")
        self.callbacks.append(vectorNodeRemovedCallbackID)
        self.callbacks.append(matrixNodeRemovedCallbackID)
        self.callbacks.append(angleNodeRemovedCallbackID)

        # NOTE(fuzes): Selection changed callback
        self.callbacks.append(om2.MEventMessage.addEventCallback("SelectionChanged", self._on_maya_selection_changed))

    # noinspection PyArgumentList
    def _on_maya_selection_changed(self, clientData):

        if not self.runSelectionCallback:
            return

        selection = self.view.selectionModel()
        selection.select(QModelIndex(), QItemSelectionModel.Clear)
        for mob in iterSelection():
            isMayaSelectionEmpty = False

            name = ""
            # NOTE(fuzes): If we are selecting a shape we can just search for it.
            # TODO(fuzes): This callback gets called all the time make sure we perform fast here!
            # TODO(fuzes): How to check for plugin types ???
            if mob.hasFn(om2.MFn.kShape):
                mfn_dep = om2.MFnDependencyNode(mob)
                name = mfn_dep.name()

            # NOTE(fuzes): Check if the shape under the transform might be a interesting object for us
            # If we find that it is a type of a ddraw node we search for it in our Tree
            if mob.hasFn(om2.MFn.kTransform):
                mfn_dag = om2.MFnDagNode(mob)
                if mfn_dag.childCount() == 1:
                    childMob = mfn_dag.child(0)
                    if getStringTypeFromMob(childMob).startswith("ddraw"):
                        mfn_dag.setObject(childMob)
                        name = mfn_dag.name()

            # NOTE(fuzes): Finally let's search for the name in our tree and if we find a match select it
            if name:
                items = self.model.match(self.model.index(0, 0), Qt.DisplayRole, name, 2, Qt.MatchRecursive)
                for index in items:
                    selection.select(index, QItemSelectionModel.Select)

    def replaceParameterWidget(self, widget):
        self.mainLayout.replaceWidget(self.replacementWidget, widget)
        self.replacementWidget.deleteLater()
        self.replacementWidget = widget

    def _on_data_changed(self):

        model = self.view.selectionModel()
        for index in model.selectedIndexes():
            item = index.internalPointer()
            if item.type != DDrawTypes.kGroup:
                mob = item.data["data"].object()
                if item.type == DDrawTypes.kVector:
                    settings = self.replacementWidget.getDrawVectorOptions()
                    setVectorAttributesFromOptions(mob, settings)
                elif item.type == DDrawTypes.kMatrix:
                    settings = self.replacementWidget.getDrawMatrixOptions()
                    setMatrixOptionsFromMob(mob, settings)
                elif item.type == DDrawTypes.kAngle:
                    settings = self.replacementWidget.getDrawAngleOptions()
                    setAngleAttributesFromOptions(mob, settings)
                else:
                    global_logger.error("_on_data_changed: Invalid type passed can not set options for node.")

    # noinspection PyArgumentList
    def _on_tree_view_selection_changed(self, selected, deselected):

        self.runSelectionCallback = False
        self.replaceParameterWidget(QWidget())
        for index in selected.indexes():
            item = index.internalPointer()
            if item.type != DDrawTypes.kGroup:
                mob = item.data["data"].object()
                if item.type == DDrawTypes.kVector:
                    widget = DDrawVectorParametersWidget(getVectorOptionsFromMob(mob), self)
                    self.replaceWithDrawWidgetAndConnect(widget)
                elif item.type == DDrawTypes.kMatrix:
                    widget = DDrawMatrixParametersWidget(getMatrixOptionsFromMob(mob), self)
                    self.replaceWithDrawWidgetAndConnect(widget)
                elif item.type == DDrawTypes.kAngle:
                    widget = DDrawAngleParametersWidget(getAngleOptionsFromMob(mob), self)
                    self.replaceWithDrawWidgetAndConnect(widget)
                else:
                    global_logger.error("_on_tree_view_selection_changed: Invalid type passed")

        self.runSelectionCallback = True

    def replaceWithDrawWidgetAndConnect(self, widget):
        self.mainLayout.replaceWidget(self.replacementWidget, widget)
        self.replacementWidget.deleteLater()
        self.replacementWidget = widget
        self.replacementWidget.dataChanged.connect(self._on_data_changed)

    def _on_ddraw_node_added(self, mob, clientData):

        data = getDataFromMob(mob)
        index = None
        if clientData == DDrawTypes.kVector:
            index = self.model.index(0, 0)
        elif clientData == DDrawTypes.kMatrix:
            index = self.model.index(1, 0)
        elif clientData == DDrawTypes.kAngle:
            index = self.model.index(2, 0)
        else:
            global_logger.error("_on_ddraw_node_added callback failed: ClientData is invalid.")

        model = self.model
        model.insertRow(0, index)
        child = model.index(0, 0, index)

        model.setData(child, [clientData, data], Qt.EditRole)

    # noinspection PyArgumentList
    def nodeRemovedCallback(self, mob, clientData):

        mfn_dep = om2.MFnDependencyNode(mob)
        self.removeItemFromName(mfn_dep.name())

    def removeItemFromName(self, name):
        items = self.model.match(self.model.index(0, 0), Qt.DisplayRole, name, 2, Qt.MatchRecursive)
        if items:
            index = items[0]
            self.model.removeRow(index.row(), index.parent())
        else:
            global_logger.info("No valid item found to be deleted: {}".format(name))

    def removeRow(self):

        for index in self.view.selectionModel().selectedIndexes():
            item = index.internalPointer()
            data = item.data
            itemData = data["data"]
            if itemData:
                mob = itemData.object()
                if not mob.isNull():
                    # NOTE(fuzes): We let the nodeRemovedCallback handle the deletion from the TreeView
                    deleteDDrawMob(mob)
                    #model.removeRow(index.row(), index.parent())
            else:
                cmds.warning("Can not delete top group: {}".format(data["displayName"]))

    def closeEvent(self, event):

        for i in self.callbacks:
            om2.MMessage.removeCallback(i)
        self.callbacks.clear()

# noinspection PyArgumentList,PyArgumentList
def deleteDDrawMob(mob):
    """
    Convenience function for deleting the transform from the given [MObject] shape node.
    So we do not leave any stray nodes.
    :param mob: [MObject] the shape from which to find the transform and delete it
    :return: [bool] Wheter we deleted something or not
    """
    if not mob.hasFn(om2.MFn.kShape):
        return False
    mfn_dag = om2.MFnDagNode(mob)
    parentMob = mfn_dag.parent(0)
    if parentMob.isNull():
        return False
    mfn_dag_parent = om2.MFnDagNode(parentMob)
    cmds.delete(mfn_dag_parent.fullPathName())
    return True

def RunDDrawWindow(*args):
    if not cmds.pluginInfo("debugDraw.mll", q=True, l=True):
        print "Not loaded can not Run DDraw Window"
        return

    if cmds.window(DDRAW_WINDOW_NAME, ex = True):
        cmds.deleteUI(DDRAW_WINDOW_NAME)
    app = DDrawWindow()
    app.show()

_MENU_NAME = "ddraw_marking_menu"

def createDDrawMarkingMenu():
    initMarkingMenu(_MENU_NAME)

    cmds.menuItem(p=_MENU_NAME, l="Draw Vector", rp="N", c=DrawVectorFromQSettings, i=":/nodeGrapherArrowUp")
    cmds.menuItem(p=_MENU_NAME, ob=True, c=RunVectorOptions)
    cmds.menuItem(p=_MENU_NAME, l="Draw Matrix", rp="E", c=DrawMatrixFromQSettings, i=":/out_addMatrix")
    cmds.menuItem(p=_MENU_NAME, ob=True, c=RunMatrixOptions)
    cmds.menuItem(p=_MENU_NAME, l="Draw Angle", rp="S", c=DrawAngleFromQSettings, i=":/angleBetween")
    cmds.menuItem(p=_MENU_NAME, ob=True, c=RunAngleOptions)
    cmds.menuItem(p=_MENU_NAME, l="DDraw Window", rp="W", c=RunDDrawWindow, i=":/menuIconWindow")

    cmds.menuItem(p=_MENU_NAME, l="Default Vector Attribute", c=partial(runSaveDefaultAttributeDialog,
                                                                            DDrawTypes.kVector))
    cmds.menuItem(p=_MENU_NAME, l="Default Matrix Attribute", c=partial(runSaveDefaultAttributeDialog,
                                                                            DDrawTypes.kMatrix))

global_logger = logging.getLogger("ddraw_loger")










