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
#include <maya/MMatrix.h>

class DDrawMatrixData : public MUserData
{
    public:
    DDrawMatrixData() : MUserData(false){};
    virtual ~DDrawMatrixData() {};
    
    MVector Position;
    
    MVector XAxis;
    MVector YAxis;
    MVector ZAxis;
    
    MColor TextColor;
    b32 DisplayText;
};

class DDrawMatrixDrawOverride : public MHWRender::MPxDrawOverride
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
    DDrawMatrixDrawOverride(const MObject &obj);
};