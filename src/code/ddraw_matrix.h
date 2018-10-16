#pragma once

#include <maya/M3dView.h>
#include <maya/MBoundingBox.h>
#include <maya/MDagPath.h>
#include <maya/MDataBlock.h>
#include <maya/MObject.h>
#include <maya/MGlobal.h>
#include <maya/MPlug.h>
#include <maya/MPxLocatorNode.h>
#include <maya/MString.h>
#include <maya/MStatus.h>
#include <maya/MTypeId.h>
#include <maya/MFloatVector.h>
#include <maya/MColor.h>
#include <maya/MGL.h>
#include <maya/MPoint.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnDependencyNode.h>
#include <maya/MFnDagNode.h>
#include <maya/MFnMatrixAttribute.h>
#include <maya/MMatrix.h>

class DDrawMatrix : public MPxLocatorNode
{
    public:
    DDrawMatrix();
    virtual ~DDrawMatrix();
    
    static void* creator();
    static MStatus initialize();
    
    static MStatus compute(const MPlug& plug, MDataBlock& dataBlock);
    
    
    virtual bool isBounded() const;
    virtual MBoundingBox boundingBox() const;
    virtual void draw(M3dView& view, const MDagPath &path,
                      M3dView::DisplayStyle style,
                      M3dView::DisplayStatus displayStatus);
    
    virtual void postConstructor();
    
    // NOTE(fuzes): For the simple dependency node
    static MString Name;
    static MTypeId Id;
    
    // NOTE(fuzes): For the Viewport 2.0 renderer
    static MString drawClassification;
    static MString drawRegistrantID;
    
    // NOTE(fuzes): Attributes on the node
    static MObject aInMatrix;
    static MObject aDisplayText;
    static MObject aTextColor;
};
