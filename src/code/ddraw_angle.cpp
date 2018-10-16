#include "ddraw_angle.h"

MString DDrawAngle::Name = "ddraw_angle";
MString DDrawAngle::drawClassification = "drawdb/geometry/angle_lib/ddraw_angle";
MString DDrawAngle::drawRegistrantID = "angle_lib";
// NOTE(fuzes): Your Node ID Block is: 0x0012e180 - 0x0012e1bf
MTypeId DDrawAngle::Id = 0x0012e181;

MObject DDrawAngle::aV1;
MObject DDrawAngle::aV2;
MObject DDrawAngle::aOrigin;
MObject DDrawAngle::aTextColor;
MObject DDrawAngle::aNormalize;

DDrawAngle::DDrawAngle()
{
    
}

DDrawAngle::~DDrawAngle()
{
    
}

void
DDrawAngle::postConstructor()
{
    MObject oThis = thisMObject();
    MFnDependencyNode fnNode( oThis );
    fnNode.setName( "ddraw_angleShape#" );
    MFnDagNode fnDagNode(oThis);
    MObject TransformMob = fnDagNode.parent(0);
    MFnDagNode fnParent(TransformMob);
    fnParent.setName("ddraw_angle#");
}

void*
DDrawAngle::creator()
{
    return new DDrawAngle();
}

MStatus
DDrawAngle::initialize()
{
    MFnNumericAttribute nAttr;
    
    aV1 = nAttr.createPoint("vector1", "vector1");
    nAttr.setKeyable(true);
    nAttr.setDefault(1.0f, 0.0f, 0.0f);
    addAttribute(aV1);
    
    aV2 = nAttr.createPoint("vector2", "vector2");
    nAttr.setKeyable(true);
    nAttr.setDefault(0.0f, 1.0f, 0.0f);
    addAttribute(aV2);
    
    aOrigin= nAttr.createPoint("origin", "origin");
    nAttr.setKeyable(true);
    addAttribute(aOrigin);
    
    aTextColor = nAttr.createColor("textColor", "textColor");
    nAttr.setKeyable(true);
    nAttr.setDefault(1.0f, 1.0f, 1.0f);
    addAttribute(aTextColor);
    
    aNormalize = nAttr.create("normalize", "normalize", MFnNumericData::kBoolean, 1);
    nAttr.setKeyable(true);
    addAttribute(aNormalize);
    
    return MS::kSuccess;
}

MStatus
DDrawAngle::compute(const MPlug& plug, MDataBlock& dataBlock)
{
    return MStatus::kSuccess;
}

bool
DDrawAngle::isBounded() const
{
    return true;
}

MBoundingBox
DDrawAngle::boundingBox() const
{
    MPoint Corner1(-1.0, 0.0, -1.0);
    MPoint Corner2(1.0, 0.0, -1.0);
    
    return MBoundingBox(Corner1, Corner2);
}

void
DDrawAngle::draw(M3dView& view, const MDagPath &path,
                 M3dView::DisplayStyle style,
                 M3dView::DisplayStatus displayStatus)
{
    // NOTE(fuzes): We are not supporting legacy viewport ?!
}
