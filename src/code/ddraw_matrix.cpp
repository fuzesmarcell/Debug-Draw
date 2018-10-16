#include "ddraw_matrix.h"

MString DDrawMatrix::Name = "ddraw_matrix";
MString DDrawMatrix::drawClassification = "drawdb/geometry/ddraw_matrix";
MString DDrawMatrix::drawRegistrantID = "matrix_lib";
// NOTE(fuzes): Your Node ID Block is: 0x0012e180 - 0x0012e1bf
MTypeId DDrawMatrix::Id = 0x0012e182;

MObject DDrawMatrix::aInMatrix;
MObject DDrawMatrix::aDisplayText;
MObject DDrawMatrix::aTextColor;

DDrawMatrix::DDrawMatrix()
{
    
}

DDrawMatrix::~DDrawMatrix()
{
    
}

void
DDrawMatrix::postConstructor()
{
    MObject oThis = thisMObject();
    MFnDependencyNode fnNode( oThis );
    fnNode.setName( "ddraw_matrixShape#" );
    MFnDagNode fnDagNode(oThis);
    MObject TransformMob = fnDagNode.parent(0);
    MFnDagNode fnParent(TransformMob);
    fnParent.setName("ddraw_matrix#");
}

void*
DDrawMatrix::creator()
{
    return new DDrawMatrix();
}


MStatus
DDrawMatrix::initialize()
{
    MFnMatrixAttribute mAttr;
    MFnNumericAttribute nAttr;
    
    aInMatrix = mAttr.create("inMatrix", "inMatrix");
    addAttribute(aInMatrix);
    
    aTextColor = nAttr.createColor("textColor", "textColor");
    nAttr.setKeyable(true);
    nAttr.setDefault(1.0f, 1.0f, 1.0f);
    addAttribute(aTextColor);
    
    aDisplayText =
        nAttr.create("displayText", "displayText", MFnNumericData::kBoolean, 0);
    nAttr.setKeyable(true);
    addAttribute(aDisplayText);
    
    return MS::kSuccess;
}


MStatus
DDrawMatrix::compute(const MPlug& plug, MDataBlock& dataBlock)
{
    return MStatus::kSuccess;
}

bool
DDrawMatrix::isBounded() const
{
    return true;
}

MBoundingBox
DDrawMatrix::boundingBox() const
{
    MPoint Corner1(-1.0, 0.0, -1.0);
    MPoint Corner2(1.0, 0.0, -1.0);
    
    return MBoundingBox(Corner1, Corner2);
}

void
DDrawMatrix::draw(M3dView& view, const MDagPath &path,
                  M3dView::DisplayStyle style,
                  M3dView::DisplayStatus displayStatus)
{
    // NOTE(fuzes): We are not supporting legacy viewport ?!
}


