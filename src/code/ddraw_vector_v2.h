#include <maya/MDrawContext.h>
#include <maya/MPxDrawOverride.h>
#include <maya/MUserData.h>

#include <maya/MBoundingBox.h>
#include <maya/MColor.h>
#include <maya/MDagPath.h>
#include <maya/MGlobal.h>
#include <maya/MObject.h>
#include <maya/MPoint.h>
#include <maya/MVector.h>

class DDrawVectorData : public MUserData
{
    public:
    DDrawVectorData() : MUserData(false){};
    virtual ~DDrawVectorData() {};
    
    MVector origin;
    MVector vectorPoint;
    MVector endPoint;
    
    f32 magnitude;
    MPoint magnitudeDrawPosition;
    
    MColor vectorColor;
    MColor textColor;
    
    f32 coneRadius;
    f32 coneHeight;
    b32 displayText;
    
    M3dView::DisplayStatus status;
};

class DDrawVectorDrawOverride : public MHWRender::MPxDrawOverride
{
    public:
    static MHWRender::MPxDrawOverride* create(const MObject& obj);
    
    virtual MHWRender::DrawAPI supportedDrawAPIs() const;
    
    virtual bool isBounded(const MDagPath &objPath,
                           const MDagPath& cameraPath) const;
    
    virtual MBoundingBox boundingBox(const MDagPath &objPath,
                                     const MDagPath& cameraPath) const;
    
    virtual bool hasUIDrawables() const { return true; }
    
    virtual MUserData* prepareForDraw(const MDagPath& objPath,
                                      const MDagPath& cameraPath,
                                      const MHWRender::MFrameContext& frameContext,
                                      MUserData* oldData);
    
    virtual void addUIDrawables(const MDagPath &objPath,
                                MHWRender::MUIDrawManager& drawManager,
                                const MHWRender::MFrameContext& frameContext,
                                const MUserData* data);
    private:
    DDrawVectorDrawOverride(const MObject &obj);
};