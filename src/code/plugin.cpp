#include <stdint.h>

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;

typedef int8_t s8;
typedef int16_t s16;
typedef int32_t s32;
typedef int64_t s64;
typedef s32 b32;

typedef float f32;
typedef double f64;

#include "ddraw_vector.cpp"
#include "ddraw_vector_v2.cpp"

#include "ddraw_angle.cpp"
#include "ddraw_angle_v2.cpp"

#include "ddraw_matrix.cpp"
#include "ddraw_matrix_v2.cpp"

#include <maya/MFnPlugin.h>
#include <maya/MDrawRegistry.h>

#include <maya/MGlobal.h>

// TODO(fuzes): Export the symbols in our batch file would make it easier
__declspec(dllexport)
MStatus
initializePlugin(MObject obj)
{
    MStatus status;
    
    MFnPlugin fn(obj);
    
    //
    // Vector node register
    //
    
    MString *vectorClassification = &DDrawVector::drawClassification;
    
    status = fn.registerNode(DDrawVector::Name,
                             DDrawVector::Id,
                             DDrawVector::creator,
                             DDrawVector::initialize,
                             MPxNode::kLocatorNode,
                             vectorClassification
                             );
    CHECK_MSTATUS_AND_RETURN_IT(status);
    
    status = MHWRender::MDrawRegistry::
        registerDrawOverrideCreator(DDrawVector::drawClassification,
                                    DDrawVector::drawRegistrantID,
                                    DDrawVectorDrawOverride::create);
    CHECK_MSTATUS_AND_RETURN_IT(status);
    
    //
    // Angle node register
    //
    
    MString *angleClassification = &DDrawAngle::drawClassification;
    
    fn.registerNode(DDrawAngle::Name,
                    DDrawAngle::Id,
                    DDrawAngle::creator,
                    DDrawAngle::initialize,
                    MPxNode::kLocatorNode,
                    angleClassification
                    );
    
    MHWRender::MDrawRegistry::
        registerDrawOverrideCreator(DDrawAngle::drawClassification,
                                    DDrawAngle::drawRegistrantID,
                                    DDrawAngleDrawOverride::create);
    
    //
    // Matrix node register
    //
    
    MString *matrixClassification = &DDrawMatrix::drawClassification;
    
    fn.registerNode(DDrawMatrix::Name,
                    DDrawMatrix::Id,
                    DDrawMatrix::creator,
                    DDrawMatrix::initialize,
                    MPxNode::kLocatorNode,
                    matrixClassification
                    );
    
    MHWRender::MDrawRegistry::
        registerDrawOverrideCreator(DDrawMatrix::drawClassification,
                                    DDrawMatrix::drawRegistrantID,
                                    DDrawMatrixDrawOverride::create);
    
    //
    // Creating the menu
    // 
    
    return MStatus::kSuccess;
}

__declspec(dllexport)
MStatus
uninitializePlugin(MObject obj)
{
    MFnPlugin fn(obj);
    
    
    //
    // Vector node deregister
    //
    
    fn.deregisterNode(DDrawVector::Id);
    MHWRender::MDrawRegistry::
        deregisterDrawOverrideCreator(
        DDrawVector::drawClassification,
        DDrawVector::drawRegistrantID
        );
    
    //
    // Angle node deregister
    //
    
    fn.deregisterNode(DDrawAngle::Id);
    MHWRender::MDrawRegistry::
        deregisterDrawOverrideCreator(
        DDrawAngle::drawClassification,
        DDrawAngle::drawRegistrantID
        );
    
    //
    // Matrix node deregister
    //
    
    fn.deregisterNode(DDrawMatrix::Id);
    MHWRender::MDrawRegistry::
        deregisterDrawOverrideCreator(
        DDrawMatrix::drawClassification,
        DDrawMatrix::drawRegistrantID
        );
    
    return MStatus::kSuccess;
}
