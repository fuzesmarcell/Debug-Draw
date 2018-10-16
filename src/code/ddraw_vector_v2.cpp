#include "ddraw_vector_v2.h"

DDrawVectorDrawOverride::DDrawVectorDrawOverride
(const MObject& obj) : MHWRender::MPxDrawOverride(obj, NULL)
{
    
}

MHWRender::MPxDrawOverride* 
DDrawVectorDrawOverride::create(const MObject& obj)
{
    return new DDrawVectorDrawOverride(obj);
}

MHWRender::DrawAPI
DDrawVectorDrawOverride::supportedDrawAPIs() const
{
    return (MHWRender::kOpenGL |
            MHWRender::kOpenGLCoreProfile |
            MHWRender::kDirectX11);
}

bool
DDrawVectorDrawOverride::isBounded(const MDagPath &objPath,
                                   const MDagPath& cameraPath) const
{
    return false;
}

MBoundingBox
DDrawVectorDrawOverride::boundingBox(const MDagPath &objPath,
                                     const MDagPath& cameraPath) const
{
    MPoint Corner1(-1.0, 0.0, -1.0);
    MPoint Corner2(1.0, 0.0, -1.0);
    
    return MBoundingBox(Corner1, Corner2);
}

static MVector
GetMVectorFromCompound(MPlug Plug)
{
    MVector Result = {};
    
    if(Plug.isCompound())
    {
        u32 NumChild = Plug.numChildren();
        f64 Points[3];
        // TODO(fuzes): Are we sure that the order in which we get the
        // attributes matches the x,y,z order ?
        for(u32  Index = 0;
            Index < NumChild;
            ++Index)
        {
            MPlug ChildPlug = Plug.child(Index);
            Points[Index] = ChildPlug.asFloat();
        }
        
        Result = MVector(Points[0], Points[1], Points[2]);
    }
    else
    {
        // NOTE(fuzes): The given plug is not a compound
    }
    
    return Result;
}


static MColor
GetMColorFromCompound(MPlug Plug)
{
    MColor Result = {};
    
    if(Plug.isCompound())
    {
        u32 NumChild = Plug.numChildren();
        f64 Points[3];
        // TODO(fuzes): Are we sure that the order in which we get the
        // attributes matches the r,g,b order ?
        for(u32  Index = 0;
            Index < NumChild;
            ++Index)
        {
            MPlug ChildPlug = Plug.child(Index);
            Points[Index] = ChildPlug.asFloat();
        }
        
        Result = MColor((f32)Points[0], (f32)Points[1], (f32)Points[2]);
    }
    else
    {
        // NOTE(fuzes): The given plug is not a compound
    }
    
    return Result;
}


MUserData*
DDrawVectorDrawOverride::prepareForDraw(const MDagPath& objPath,
                                        const MDagPath& cameraPath,
                                        const MHWRender::MFrameContext& frameContex,
                                        MUserData* oldData)
{
    DDrawVectorData* data = (DDrawVectorData *)oldData;
    
    if(!data)
    {
        data = new DDrawVectorData();
    }
    
    MObject obj = objPath.node();
    
    
    data->status = M3dView::displayStatus(objPath);
    
    // NOTE(fuzes): Retrieve from the node attributes
    MVector Origin = 
        GetMVectorFromCompound(MPlug(obj, DDrawVector::aOrigin));
    MVector EndPoint = 
        GetMVectorFromCompound(MPlug(obj, DDrawVector::aEndPoint));
    MColor VectorColor = 
        GetMColorFromCompound(MPlug(obj, DDrawVector::aVectorColor));
    MColor TextColor = 
        GetMColorFromCompound(MPlug(obj, DDrawVector::aTextColor));
    f32 ConeHeight = MPlug(obj, DDrawVector::aConeHeight).asFloat();
    f32 ConeRadius = MPlug(obj, DDrawVector::aConeRadius).asFloat();
    b32 DisplayText = MPlug(obj, DDrawVector::aDisplayText).asBool();
    
    // NOTE(fuzes): Our own calculations
    MVector WrldEndPoint = EndPoint + Origin;
    f32 Magnitude = (f32)EndPoint.length();
    
    MVector Direction = EndPoint.normal();
    MVector MagnitudeDrawPosition = Origin + (Direction * (Magnitude / 2.0f));
    
    data->origin = Origin;
    data->vectorPoint = EndPoint;
    data->endPoint = WrldEndPoint;
    
    data->magnitude = Magnitude;
    data->magnitudeDrawPosition = MagnitudeDrawPosition;
    
    data->vectorColor = VectorColor;
    data->textColor = TextColor;
    
    data->coneRadius = ConeRadius;
    data->coneHeight = ConeHeight;
    data->displayText = DisplayText;
    
    return data;
}

static void
DrawVector(MHWRender::MUIDrawManager& drawManager,
           MVector Origin, MVector End, MColor Color,
           f32 ConeHeight = 0.1f, f32 ConeRadius = 0.05f)
{
    MVector WrlEndPoint = End + Origin;
    f32 Magnitude = (f32)End.length();
    
    MVector Direction = End.normal();
    
    MVector DrawPosition = ((Magnitude - ConeHeight) *
                            Direction) + Origin;
    
    drawManager.beginDrawable();
    drawManager.setColor(Color);
    
    drawManager.setLineWidth(2);
    drawManager.line(Origin, DrawPosition);
    drawManager.cone(DrawPosition, Direction,
                     ConeRadius, ConeHeight,
                     true);
    
    drawManager.endDrawable();
    
}

void
DDrawVectorDrawOverride::addUIDrawables(const MDagPath &objPath,
                                        MHWRender::MUIDrawManager& drawManager,
                                        const MHWRender::MFrameContext& context,
                                        const MUserData* data)
{
    DDrawVectorData* NewData = (DDrawVectorData *)data;
    if(!NewData)
    {
        return;
    }
    
    MColor vectorColor, textColor;
    if (NewData->status == M3dView::kActive)
    {
        vectorColor = MColor(1.0f, 1.0f, 1.0f);
        textColor = MColor(1.0f, 1.0f, 1.0f);
    }
    else if(NewData->status == M3dView::kLead)
    {
        vectorColor = MColor( .26f, 1.0f, .64f);
        textColor = MColor( .26f, 1.0f, .64f);
    }
    else
    {
        vectorColor = NewData->vectorColor;
        textColor = NewData->textColor;
    }
    
    DrawVector(drawManager,
               NewData->origin, NewData->vectorPoint,
               vectorColor,
               NewData->coneHeight, NewData->coneRadius);
    
    if(NewData->displayText)
    {    
        drawManager.beginDrawable();
        drawManager.setColor(textColor);
        char EndPointBuffer[256];
        _snprintf_s(EndPointBuffer, sizeof(EndPointBuffer),
                    "{%.02f, %.02f, %.02f} \n",
                    NewData->endPoint.x,
                    NewData->endPoint.y,
                    NewData->endPoint.z);
        
        char LenghtBuffer[30];
        _snprintf_s(LenghtBuffer, sizeof(LenghtBuffer), "%.02f", NewData->magnitude);
        
        drawManager.text(NewData->endPoint, EndPointBuffer,
                         MHWRender::MUIDrawManager::TextAlignment::kCenter);
        
        drawManager.text(NewData->magnitudeDrawPosition,
                         LenghtBuffer);
        
        drawManager.endDrawable();
    }
    
    
}