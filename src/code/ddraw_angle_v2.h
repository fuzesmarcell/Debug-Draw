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
#include <maya/MPointArray.h>

class DDrawAngleData : public MUserData
{
    public:
    DDrawAngleData() : MUserData(false){};
    virtual ~DDrawAngleData() {};
    
    MVector V1;
    MVector V2;
    MVector origin;
    MVector plane;
    
    f32 radians;
    f32 degrees;
    
    MColor textColor;
};

class DDrawAngleDrawOverride : public MHWRender::MPxDrawOverride
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
    DDrawAngleDrawOverride(const MObject &obj);
};