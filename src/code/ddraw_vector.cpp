#include "ddraw_vector.h"

MString DDrawVector::Name = "ddraw_vector";
MString DDrawVector::drawClassification = "drawdb/geometry/ddraw_vector";
MString DDrawVector::drawRegistrantID = "ddrawNodePlugin";

// NOTE(fuzes): Your Node ID Block is: 0x0012e180 - 0x0012e1bf
MTypeId DDrawVector::Id = 0x0012e180;

MObject DDrawVector::aOrigin;
MObject DDrawVector::aEndPoint;
MObject DDrawVector::aVectorColor;
MObject DDrawVector::aTextColor;
MObject DDrawVector::aConeRadius;
MObject DDrawVector::aConeHeight;
MObject DDrawVector::aDisplayText;

DDrawVector::DDrawVector()
{
    
}

DDrawVector::~DDrawVector()
{
    
}

void
DDrawVector::postConstructor()
{
    MObject oThis = thisMObject();
    MFnDependencyNode fnNode( oThis );
    fnNode.setName( "ddraw_vectorShape#" );
    MFnDagNode fnDagNode(oThis);
    MObject TransformMob = fnDagNode.parent(0);
    MFnDagNode fnParent(TransformMob);
    fnParent.setName("ddraw_vector#");
}


void*
DDrawVector::creator()
{
    return new DDrawVector();
}

MStatus
DDrawVector::initialize()
{
    MFnNumericAttribute nAttr;
    
    aOrigin = nAttr.createPoint("origin", "origin");
    nAttr.setKeyable(true);
    addAttribute(aOrigin);
    
    aEndPoint = nAttr.createPoint("endPoint", "endPoint");
    nAttr.setKeyable(true);
    nAttr.setDefault(0.0f, 1.0f, 0.0f);
    addAttribute(aEndPoint);
    
    aVectorColor = nAttr.createColor("vectorColor", "vectorColor");
    nAttr.setKeyable(true);
    nAttr.setDefault(0.0f, 0.4f, 1.0f);
    addAttribute(aVectorColor);
    
    aTextColor = nAttr.createColor("textColor", "textColor");
    nAttr.setKeyable(true);
    nAttr.setDefault(1.0f, 1.0f, 1.0f);
    addAttribute(aTextColor);
    
    aConeRadius = nAttr.create("coneRadius", "coneRadius", MFnNumericData::kFloat,
                               0.1f);
    nAttr.setKeyable(true);
    nAttr.setMin(0.0);
    addAttribute(aConeRadius);
    
    aConeHeight = nAttr.create("coneHeight", "coneHeight", MFnNumericData::kFloat,
                               0.2f);
    nAttr.setMin(0.0);
    nAttr.setKeyable(true);
    addAttribute(aConeHeight);
    
    aDisplayText =
        nAttr.create("displayText", "displayText", MFnNumericData::kBoolean, 1);
    nAttr.setKeyable(true);
    addAttribute(aDisplayText);
    
    return MStatus::kSuccess;
}

MStatus
DDrawVector::compute(const MPlug& plug, MDataBlock& dataBlock)
{
    return MStatus::kSuccess;
}

bool
DDrawVector::isBounded() const
{
    return true;
}

MBoundingBox
DDrawVector::boundingBox() const
{
    MPoint Corner1(-1.0, 0.0, -1.0);
    MPoint Corner2(1.0, 0.0, -1.0);
    
    return MBoundingBox(Corner1, Corner2);
}

void
DDrawVector::draw(M3dView& view, const MDagPath &path,
                  M3dView::DisplayStyle style,
                  M3dView::DisplayStatus displayStatus)
{
    // NOTE(fuzes): We are not supporting legacy viewport ?!
}