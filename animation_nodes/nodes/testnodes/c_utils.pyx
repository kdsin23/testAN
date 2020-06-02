import cython
from libc.math cimport sqrt
from .. matrix.c_utils import* 
from ... math cimport abs as absNumber
from mathutils import Matrix, Euler, Vector
from ... math import matrix4x4ListToEulerList
from ... libs.FastNoiseSIMD.wrapper import PyNoise
from ... algorithms.lists.random import generateRandomVectors
from ... algorithms.random import uniformRandomDoubleWithTwoSeeds, getRandom3DVector
from ... nodes.number.c_utils import range_DoubleList_StartStop, mapRange_DoubleList_Interpolated 
from ... data_structures cimport (
    DoubleList, FloatList,VirtualMatrix4x4List,
    Vector3DList, EulerList, Matrix4x4List,
    VirtualVector3DList, VirtualEulerList, VirtualFloatList, VirtualDoubleList,
    Action, ActionEvaluator, PathIndexActionChannel,
    BoundedAction, BoundedActionEvaluator,Color,
    ColorList, PolygonIndicesList, IntegerList, PolySpline, BezierSpline, Interpolation
)
from ... math cimport (
    add, subtract, multiply, divide_Save, modulo_Save,
    sin, cos, tan, asin_Save, acos_Save, atan, atan2, hypot,
    power_Save, floor, ceil, sqrt_Save, invert, reciprocal_Save,
    snap_Save, copySign, floorDivision_Save, logarithm_Save,
    Vector3, Euler3, Matrix4, toMatrix4,toVector3,multMatrix4, toPyMatrix4,
    invertOrthogonalTransformation,setTranslationRotationScaleMatrix,
    setRotationXMatrix, setRotationYMatrix, setRotationZMatrix,
    setRotationMatrix, setTranslationMatrix, setIdentityMatrix,
    setScaleMatrix,setMatrixTranslation,transposeMatrix_Inplace
)
from ... algorithms.lists.random import generateRandomVectors
from ... utils.limits cimport INT_MAX
from ... algorithms.random import getUniformRandom


def VectorsToColors(Vector3DList vectors):
    cdef Py_ssize_t count = vectors.getLength()
    cdef Py_ssize_t i
    cdef ColorList colors = ColorList(length = count)
    for i in range(count):
        r = absNumber(vectors.data[i].x)
        g = absNumber(vectors.data[i].y)
        b = absNumber(vectors.data[i].z)
        colors.data[i] = Color(r, g, b, 1)
    return colors

def matrix_lerp(Matrix4x4List mA, Matrix4x4List mB, DoubleList influences):
    cdef Vector3DList tA = extractMatrixTranslations(mA)
    cdef Vector3DList tB = extractMatrixTranslations(mB)
    cdef EulerList rA = extractMatrixRotations(mA)
    cdef EulerList rB = extractMatrixRotations(mB)
    cdef Vector3DList sA = extractMatrixScales(mA)
    cdef Vector3DList sB = extractMatrixScales(mB)
    cdef int count = max(mA.getLength(), mB.getLength())
    cdef VirtualVector3DList translations_out = VirtualVector3DList.create(tA, (0, 0, 0))
    cdef VirtualEulerList rotations_out = VirtualEulerList.create(rA, (0, 0, 0))
    cdef VirtualVector3DList scales_out = VirtualVector3DList.create(sA, (1, 1, 1))
    for i in range(count):
        translations_out.get(i).x = tA.data[i].x * (1-influences.data[i]) + tB.data[i].x * influences.data[i]
        translations_out.get(i).y = tA.data[i].y * (1-influences.data[i]) + tB.data[i].y * influences.data[i]
        translations_out.get(i).z = tA.data[i].z * (1-influences.data[i]) + tB.data[i].z * influences.data[i]
        rotations_out.get(i).x = rA.data[i].x * (1-influences.data[i]) + rB.data[i].x * influences.data[i]
        rotations_out.get(i).y = rA.data[i].y * (1-influences.data[i]) + rB.data[i].y * influences.data[i]
        rotations_out.get(i).z = rA.data[i].z * (1-influences.data[i]) + rB.data[i].z * influences.data[i]
        scales_out.get(i).x = sA.data[i].x * (1-influences.data[i]) + sB.data[i].x * influences.data[i]
        scales_out.get(i).y = sA.data[i].y * (1-influences.data[i]) + sB.data[i].y * influences.data[i]
        scales_out.get(i).z = sA.data[i].z * (1-influences.data[i]) + sB.data[i].z * influences.data[i]      
    return composeMatrices(count, translations_out, rotations_out, scales_out)

def vector_lerp(Vector3DList vectorsA, Vector3DList vectorsB, DoubleList influences):
    cdef Py_ssize_t count = max(vectorsA.getLength(), vectorsB.getLength())
    cdef Py_ssize_t i
    cdef Vector3DList out_vectorlist = Vector3DList(length = count)
    for i in range(count):
        out_vectorlist.data[i].x = vectorsA.data[i].x * (1-influences.data[i]) + vectorsB.data[i].x * influences.data[i]
        out_vectorlist.data[i].y = vectorsA.data[i].y * (1-influences.data[i]) + vectorsB.data[i].y * influences.data[i]
        out_vectorlist.data[i].z = vectorsA.data[i].z * (1-influences.data[i]) + vectorsB.data[i].z * influences.data[i]
    return out_vectorlist

def FilterParticles(list particles, bint Alive, bint Unborn, bint Dying, bint Dead):
    cdef Py_ssize_t i
    cdef Py_ssize_t count = len(particles)
    cdef list Filtered = list()
    for i in range(count):
        if Unborn:
            if particles[i].alive_state == 'UNBORN':
                Filtered.append(particles[i])
        if Alive:
            if particles[i].alive_state == 'ALIVE':
                Filtered.append(particles[i])
        if Dying:
            if particles[i].alive_state == 'DYING':
                Filtered.append(particles[i])
        if Dead:
            if particles[i].alive_state == 'DEAD':
                Filtered.append(particles[i])

    return Filtered

def TimeEffector(Matrix4x4List matrices, Vector3DList v, EulerList e, Vector3DList s, DoubleList times, DoubleList influences, DoubleList intvals):

    cdef Vector3DList tA = extractMatrixTranslations(matrices)
    cdef EulerList rA = extractMatrixRotations(matrices)
    cdef Vector3DList sA = extractMatrixScales(matrices)
    cdef int count = matrices.getLength()
    cdef Py_ssize_t i

    #cdef DoubleList strengths = range_DoubleList_StartStop(count, 0.00, 1.00)
    #cdef DoubleList interpolatedStrengths = mapRange_DoubleList_Interpolated(strengths, interpolation, 0, 1, 0, 1)

    cdef VirtualVector3DList translations_out = VirtualVector3DList.create(tA, (0, 0, 0))
    cdef VirtualEulerList rotations_out = VirtualEulerList.create(rA, (0, 0, 0))
    cdef VirtualVector3DList scales_out = VirtualVector3DList.create(sA, (1, 1, 1))

    for i in range(count):

        intval = intvals[i]
        time = times.data[i]

        translations_out.get(i).x = tA.data[i].x + influences.data[i] * v.data[0].x * intval*time
        translations_out.get(i).y = tA.data[i].y + influences.data[i] * v.data[0].y * intval*time
        translations_out.get(i).z = tA.data[i].z + influences.data[i] * v.data[0].z * intval*time
        rotations_out.get(i).x = rA.data[i].x + influences.data[i] * e.data[0].x * intval*time
        rotations_out.get(i).y = rA.data[i].y + influences.data[i] * e.data[0].y * intval*time
        rotations_out.get(i).z = rA.data[i].z + influences.data[i] * e.data[0].z * intval*time
        scales_out.get(i).x = sA.data[i].x + influences.data[i] * s.data[0].x * intval*time
        scales_out.get(i).y = sA.data[i].y + influences.data[i] * s.data[0].y * intval*time
        scales_out.get(i).z = sA.data[i].z + influences.data[i] * s.data[0].z * intval*time
                 
    return composeMatrices(count, translations_out, rotations_out, scales_out)

def RandomEffector(Matrix4x4List matrices, Vector3DList v, EulerList e, Vector3DList s, int seed, float factor, double scalemin, double scalemax, DoubleList influences):

    cdef Vector3DList tA = extractMatrixTranslations(matrices)
    cdef EulerList rA = extractMatrixRotations(matrices)
    cdef Vector3DList sA = extractMatrixScales(matrices)
    cdef int count = matrices.getLength()
    cdef Py_ssize_t i
    cdef int _seed = seed % INT_MAX

    cdef VirtualVector3DList translations_out = VirtualVector3DList.create(tA, (0, 0, 0))
    cdef VirtualEulerList rotations_out = VirtualEulerList.create(rA, (0, 0, 0))
    cdef VirtualVector3DList scales_out = VirtualVector3DList.create(sA, (1, 1, 1))

    cdef Vector3DList randomVectors = generateRandomVectors(seed, count, factor, normalized=True)

    for i in range(count):
    
        randvec = randomVectors.data[i]
        rsca = getUniformRandom(_seed+i,scalemin,scalemax)*factor

        translations_out.get(i).x = tA.data[i].x + influences.data[i] * v.data[0].x * randvec.x
        translations_out.get(i).y = tA.data[i].y + influences.data[i] * v.data[0].y * randvec.y
        translations_out.get(i).z = tA.data[i].z + influences.data[i] * v.data[0].z * randvec.z
        rotations_out.get(i).x = rA.data[i].x + influences.data[i] * e.data[0].x * randvec.x
        rotations_out.get(i).y = rA.data[i].y + influences.data[i] * e.data[0].y * randvec.y
        rotations_out.get(i).z = rA.data[i].z + influences.data[i] * e.data[0].z * randvec.z
        scales_out.get(i).x = sA.data[i].x + influences.data[i] * s.data[0].x * rsca
        scales_out.get(i).y = sA.data[i].y + influences.data[i] * s.data[0].y * rsca
        scales_out.get(i).z = sA.data[i].z + influences.data[i] * s.data[0].z * rsca
                 
    return composeMatrices(count, translations_out, rotations_out, scales_out)

def SplineEffector(Matrix4x4List matrices, Vector3DList v, EulerList e, Vector3DList s, Vector3DList splinePoints, DoubleList influences):

    cdef Py_ssize_t i, j
    cdef Vector3DList tA = extractMatrixTranslations(matrices)
    cdef EulerList rA = extractMatrixRotations(matrices)
    cdef Vector3DList sA = extractMatrixScales(matrices)
    cdef int count = matrices.getLength()
    cdef int splinePointCount = splinePoints.getLength()
    
    cdef VirtualVector3DList translations_out = VirtualVector3DList.create(tA, (0, 0, 0))
    cdef VirtualEulerList rotations_out = VirtualEulerList.create(rA, (0, 0, 0))
    cdef VirtualVector3DList scales_out = VirtualVector3DList.create(sA, (1, 1, 1))

    cdef Vector3DList randomVectors = generateRandomVectors(12345, count, 1.0, normalized=False)

    for i in range(count):

        randvec = randomVectors.data[i]
        j = i % splinePointCount

        translations_out.get(i).x = tA.data[i].x + influences.data[i] * (splinePoints.data[j].x - tA.data[i].x  + randvec.x * v.data[0].x)
        translations_out.get(i).y = tA.data[i].y + influences.data[i] * (splinePoints.data[j].y - tA.data[i].y  + randvec.y * v.data[0].y)
        translations_out.get(i).z = tA.data[i].z + influences.data[i] * (splinePoints.data[j].z - tA.data[i].z  + randvec.z * v.data[0].z)
        rotations_out.get(i).x = rA.data[i].x + influences.data[i] * e.data[0].x
        rotations_out.get(i).y = rA.data[i].y + influences.data[i] * e.data[0].y
        rotations_out.get(i).z = rA.data[i].z + influences.data[i] * e.data[0].z
        scales_out.get(i).x = sA.data[i].x + influences.data[i] * s.data[0].x
        scales_out.get(i).y = sA.data[i].y + influences.data[i] * s.data[0].y
        scales_out.get(i).z = sA.data[i].z + influences.data[i] * s.data[0].z

    return composeMatrices(count, translations_out, rotations_out, scales_out)

    






