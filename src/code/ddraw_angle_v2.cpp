#include "ddraw_angle_v2.h"

DDrawAngleDrawOverride::DDrawAngleDrawOverride
(const MObject& obj) : MHWRender::MPxDrawOverride(obj, NULL)
{
    
}

MHWRender::MPxDrawOverride* 
DDrawAngleDrawOverride::create(const MObject& obj)
{
    return new DDrawAngleDrawOverride(obj);
}

MHWRender::DrawAPI
DDrawAngleDrawOverride::supportedDrawAPIs() const
{
    return (MHWRender::kOpenGL |
            MHWRender::kOpenGLCoreProfile |
            MHWRender::kDirectX11);
}

bool
DDrawAngleDrawOverride::isBounded(const MDagPath &objPath,
                                  const MDagPath& cameraPath) const
{
    return false;
}

MBoundingBox
DDrawAngleDrawOverride::boundingBox(const MDagPath &objPath,
                                    const MDagPath& cameraPath) const
{
    MPoint Corner1(-1.0, 0.0, -1.0);
    MPoint Corner2(1.0, 0.0, -1.0);
    
    return MBoundingBox(Corner1, Corner2);
}

MUserData*
DDrawAngleDrawOverride::prepareForDraw(const MDagPath& objPath,
                                       const MDagPath& cameraPath,
                                       const MHWRender::MFrameContext& frameContex,
                                       MUserData* oldData)
{
    DDrawAngleData* data = (DDrawAngleData *)oldData;
    
    if(!data)
    {
        data = new DDrawAngleData();
    }
    
    MObject obj = objPath.node();
    
    MVector V1 = GetMVectorFromCompound(MPlug(obj, DDrawAngle::aV1));
    MVector V2 = GetMVectorFromCompound(MPlug(obj, DDrawAngle::aV2));
    
    b32 Normalize = MPlug(obj, DDrawAngle::aNormalize).asBool();
    if(Normalize)
    {
        V1.normalize();
        V2.normalize();
    }
    
    data->V1 = V1;
    data->V2 = V2;
    data->origin = GetMVectorFromCompound(MPlug(obj, DDrawAngle::aOrigin));
    data->plane = data->V1 ^ data->V2;
    
    data->radians = (f32)data->V1.angle(data->V2);
    data->degrees = data->radians * 57.2957795f;
    
    data->textColor = GetMColorFromCompound(MPlug(obj, DDrawAngle::aTextColor));
    
    return data;
}

void
DDrawAngleDrawOverride::addUIDrawables(const MDagPath &objPath,
                                       MHWRender::MUIDrawManager& drawManager,
                                       const MHWRender::MFrameContext& context,
                                       const MUserData* data)
{
    DDrawAngleData* NewData = (DDrawAngleData *)data;
    if(!NewData)
    {
        return;
    }
    
    DrawVector(drawManager,
               NewData->origin, NewData->V1,
               MColor(1,0,0));
    
    DrawVector(drawManager,
               NewData->origin, NewData->V2,
               MColor(0,1,0));
    
    drawManager.beginDrawable();
    
    drawManager.setLineWidth(2);
    
    f32 V1Magnitude = (f32)NewData->V1.length();
    f32 V2Magnitude = (f32)NewData->V2.length();
    f32 Mult = V2Magnitude;
    
    if(V1Magnitude < V2Magnitude)
    {
        Mult = V1Magnitude;
    }
    
    drawManager.arc(NewData->origin,
                    NewData->V1,
                    NewData->V2,
                    NewData->plane,
                    Mult * 0.3);
    
    // HACK(fuzes): Compare two float numbers if they are roughly equal
    MVector AngleVector = MVector((f64)NewData->degrees, 0 ,0);
    if(AngleVector.isEquivalent(MVector(90, 0, 0)))
    {
        MPointArray DrawPoints;
        
        f64 ReductionScale = 0.1;
        MPoint V1Reduced = (NewData->V1.normal()) * Mult * ReductionScale;
        MPoint V2Reduced = (NewData->V2.normal()) * Mult * ReductionScale;
        MPoint VAddition = V1Reduced + V2Reduced;
        
        DrawPoints.append(V1Reduced);
        DrawPoints.append(VAddition);
        DrawPoints.append(VAddition);
        DrawPoints.append(V2Reduced);
        
        drawManager.lineList(DrawPoints, false);
    }
    
    drawManager.setColor(NewData->textColor);
    char TextBuffer[256];
    _snprintf_s(TextBuffer, sizeof(TextBuffer),
                "%.02fdeg|%.02frad", NewData->degrees, NewData->radians);
    
    drawManager.text(NewData->origin, TextBuffer);
    
    drawManager.endDrawable();
}