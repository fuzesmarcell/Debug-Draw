#include "ddraw_matrix_v2.h"

DDrawMatrixDrawOverride::DDrawMatrixDrawOverride
(const MObject& obj) : MHWRender::MPxDrawOverride(obj, NULL)
{
    
}

MHWRender::MPxDrawOverride* 
DDrawMatrixDrawOverride::create(const MObject& obj)
{
    return new DDrawMatrixDrawOverride(obj);
}

MHWRender::DrawAPI
DDrawMatrixDrawOverride::supportedDrawAPIs() const
{
    return (MHWRender::kOpenGL |
            MHWRender::kOpenGLCoreProfile |
            MHWRender::kDirectX11);
}

bool
DDrawMatrixDrawOverride::isBounded(const MDagPath &objPath,
                                   const MDagPath& cameraPath) const
{
    return false;
}

MBoundingBox
DDrawMatrixDrawOverride::boundingBox(const MDagPath &objPath,
                                     const MDagPath& cameraPath) const
{
    MPoint Corner1(-1.0, 0.0, -1.0);
    MPoint Corner2(1.0, 0.0, -1.0);
    
    return MBoundingBox(Corner1, Corner2);
}


MUserData*
DDrawMatrixDrawOverride::prepareForDraw(const MDagPath& objPath,
                                        const MDagPath& cameraPath,
                                        const MHWRender::MFrameContext& frameContex,
                                        MUserData* oldData)
{
    DDrawMatrixData* data = (DDrawMatrixData *)oldData;
    
    if(!data)
    {
        data = new DDrawMatrixData();
    }
    
    MObject obj = objPath.node();
    
    MDataHandle dataHandle = MPlug(obj, DDrawMatrix::aInMatrix).asMDataHandle();
    MMatrix Matrix = dataHandle.asMatrix();
    
    f64 XAxisRow[3] = {Matrix[0][0], Matrix[0][1], Matrix[0][2]};
    f64 YAxisRow[3] = {Matrix[1][0], Matrix[1][1], Matrix[1][2]};
    f64 ZAxisRow[3] = {Matrix[2][0], Matrix[2][1], Matrix[2][2]};
    
    f64 PositionRow[3] = {Matrix[3][0], Matrix[3][1], Matrix[3][2]};
    
    data->Position = MVector(PositionRow[0], PositionRow[1], PositionRow[2]);
    data->XAxis = MVector(XAxisRow[0], XAxisRow[1], XAxisRow[2]);
    data->YAxis = MVector(YAxisRow[0], YAxisRow[1], YAxisRow[2]);
    data->ZAxis = MVector(ZAxisRow[0], ZAxisRow[1], ZAxisRow[2]);
    
    data->TextColor = GetMColorFromCompound(MPlug(obj, DDrawMatrix::aTextColor));
    data->DisplayText = MPlug(obj, DDrawMatrix::aDisplayText).asBool();
    
    return data;
}

void
DDrawMatrixDrawOverride::addUIDrawables(const MDagPath &objPath,
                                        MHWRender::MUIDrawManager& drawManager,
                                        const MHWRender::MFrameContext& context,
                                        const MUserData* data)
{
    DDrawMatrixData* NewData = (DDrawMatrixData *)data;
    if(!NewData)
    {
        return;
    }
    
    DrawVector(drawManager,
               NewData->Position, NewData->YAxis,
               MColor(0,1,0));
    
    DrawVector(drawManager,
               NewData->Position, NewData->XAxis,
               MColor(1,0,0));
    
    DrawVector(drawManager,
               NewData->Position, NewData->ZAxis,
               MColor(0,0,1));
    
    char PositionText[256];
    _snprintf_s(PositionText, sizeof(PositionText),
                "{%.02f, %.02f, %.02f} \n",
                NewData->Position.x,
                NewData->Position.y,
                NewData->Position.z);
    
    if(NewData->DisplayText)
    {    
        drawManager.beginDrawable();
        drawManager.setColor(NewData->TextColor);
        drawManager.text(NewData->Position, PositionText);
        drawManager.endDrawable();
    }
    
}