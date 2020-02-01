import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import cv2 as cv
import glob

# termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((7 * 7, 3), np.float32)
objp[:, :2] = np.mgrid[0:7, 0:7].T.reshape(-1, 2)

# Arrays to store object points and image points from all the images.
objpoints = []  # 3d point in real world space
imgpoints = []  # 2d points in image plane.
images = glob.glob('chessboards/*.png')

for fname in images:
    img = cv.imread(fname)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    # Find the chess board corners
    ret, corners = cv.findChessboardCorners(gray, (7, 7),
                                            flags=cv.CALIB_CB_ADAPTIVE_THRESH | cv.CALIB_CB_NORMALIZE_IMAGE)

    # If found, add object points, image points (after refining them)
    if ret:
        objpoints.append(objp)
        corners2 = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners)
        # Draw and display the corners
        cv.drawChessboardCorners(img, (7, 7), corners2, ret)
        plt.imshow(img)
        plt.show()

    ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)


def draw(img, corners, imgpts):
    corner = tuple(corners[0].ravel())
    img = cv.line(img, corner, tuple(imgpts[0].ravel()), (255,0,0), 5)
    img = cv.line(img, corner, tuple(imgpts[1].ravel()), (0,255,0), 5)
    img = cv.line(img, corner, tuple(imgpts[2].ravel()), (0,0,255), 5)
    return img


criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
objp = np.zeros((7*7,3), np.float32)
objp[:,:2] = np.mgrid[0:7,0:7].T.reshape(-1,2)
axis = np.float32([[3,0,0], [0,3,0], [0,0,-3]]).reshape(-1,3)

for fname in glob.glob('chessboards/c4*.png'):
    img = cv.imread(fname)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    ret, corners = cv.findChessboardCorners(gray, (7, 7), None)
    if ret:
        print(fname)
        corners2 = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

        # Find the rotation and translation vectors.
        ret, pnprvecs, pnptvecs = cv.solvePnP(objp, corners2, mtx, dist)

        # project 3D points to image plane
        imgpts, jac = cv.projectPoints(axis, pnprvecs, pnptvecs, mtx, dist)
        img = draw(img, corners2, imgpts)
        plt.imshow(img)
        plt.show()


#matrice rotation
rmatRight = cv.Rodrigues(rvecs[0])[0]
rmatLeft = cv.Rodrigues(rvecs[4])[0]

#matrice translation
rotMatRight = np.concatenate((rmatRight,tvecs[0]), axis=1)
rotMatLeft = np.concatenate((rmatLeft,tvecs[4]), axis=1)

#matrice camera
camLeft = mtx @ rotMatLeft
camRight = mtx @ rotMatRight

# matrice centre de projection
camWorldCenterLeft = np.linalg.inv(np.concatenate((rotMatLeft,[[0,0,0,1]]), axis=0)) @ np.transpose([[0,0,0,1]])
camWorldCenterRight = np.linalg.inv(np.concatenate((rotMatRight,[[0,0,0,1]]), axis=0)) @ np.transpose([[0,0,0,1]])


def plotDotWorld():
    fig = plt.figure()
    ax = plt.axes(projection='3d')

    ax.scatter3D(objp[:, 0], objp[:, 1], objp[:, 2])

    x, y, z, d = camWorldCenterLeft
    ax.scatter(x, y, z, c='g', marker='o')

    x2, y2, z2, d2 = camWorldCenterRight
    ax.scatter(x2, y2, z2, c='g', marker='o')

    plt.show()


plotDotWorld()


def crossMat(v):
    v = v[:, 0]
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])


def matFondamental(camLeft, centerRight, camRight):
    return np.array(crossMat(camLeft @ centerRight) @ camLeft @ np.linalg.pinv(camRight))


def getRed(fname):
    img = cv.imread(fname)
    red = img[:, :, 2]
    ret, mask = cv.threshold(red, 127, 255, cv.THRESH_TOZERO)
    return mask


def getEpiLines(F, points):
    return F @ points


def findEpilines(path):
    epilines = []

    for l in range(26):
        if l < 10:
            strp = path + '000' + str(l) + '.png'
        else:
            strp = path + '00' + str(l) + '.png'

        red = getRed(strp)
        tempEpilines = []
        pointsLeft = [[], [], []]

        for i, line in enumerate(red):
            for pixel in line:
                if pixel != 0:
                    pixel = 1
            try:
                pointsLeft[0].append(np.average(range(1920), weights=line))
                pointsLeft[1].append(i)
                pointsLeft[2].append(1)
            except:
                pass

        epilinesRight = getEpiLines(Fondamental, pointsLeft)
        tempEpilines.append(pointsLeft)
        tempEpilines.append(epilinesRight)
        epilines.append(tempEpilines)
    return epilines


Fondamental = matFondamental(camRight, camWorldCenterLeft, camLeft)
# epl = [ [ [Red_x_avg], [Y_avg], [1] ], [EpilineRight(i)] ] ]
epl = findEpilines('scanLeft/')


def drawAvgPoint(fname, EplLeft):
    img = cv.imread(fname)
    i = 0
    while i < len(EplLeft[0]):
        color = tuple(np.random.randint(0, 255, 3).tolist())
        img = cv.circle(img, (int(EplLeft[0][i]), int(EplLeft[1][i])), 5, color, -1)
        i += 10
    plt.imshow(img)
    plt.show()


def lineY(coef, x):
    a, b, c = coef
    return -(c + a * x) / b


def drawEpl(fname, EplRight):
    img = cv.imread(fname)
    coef, length = EplRight.shape
    for i in range(0, length, 40):
        print(EplRight[:, i])
        plt.plot([0, 1919], [lineY(EplRight[:, i], 0), lineY(EplRight[:, i], 1919)], 'r')

    plt.imshow(img)
    plt.show()


drawAvgPoint('scanLeft/0013.png', epl[13][0])
drawEpl('scanRight/scan0013.png', epl[13][1])


def getReddAvg(fname):
    red = getRed(fname)
    redPoints = [[], [], []]

    for i, line in enumerate(red):
        for pixel in line:
            if pixel != 0:
                pixel = 1
        try:
            redPoints[0].append(np.average(range(1920), weights=line))
            redPoints[1].append(i)
            redPoints[2].append(1)
        except:
            pass
    return redPoints


def eplRedPoints(path, EplRight):
    points = []
    for l in range(26):
        if l < 10:
            strp = path + '000' + str(l) + '.png'
        else:
            strp = path + '00' + str(l) + '.png'

        redPoints = getReddAvg(strp)
        scan = cv.imread(strp)

        pointsRight = [[], [], []]
        eplImg = EplRight[l][1]
        print(strp)
        for i in range(len(eplImg[0])):
            try:
                x = int(redPoints[0][i])
                y = int(lineY(eplImg[:, i], x))
                pointsRight[0].append(x)
                pointsRight[1].append(y)
                pointsRight[2].append(1)

                color = tuple(np.random.randint(0, 255, 3).tolist())
                scan = cv.circle(scan, (x, y), 5, color, -1)
            except:
                pass
        points.append(pointsRight)
        # plt.imshow(scan)
        # plt.show()
    return points


pointsRight = eplRedPoints('scanRight/scan', epl)

from mathutils import geometry as pygeo
from mathutils import Vector
import json


def arrayToVector(p):
    return Vector((p[0], p[1], p[2]))


def getIntersection(pointsLeft, pointsRight):
    pL = np.array(pointsLeft)
    pR = np.array(pointsRight)

    camCenterRight = np.transpose(camWorldCenterRight)[0]
    camCenterLeft = np.transpose(camWorldCenterLeft)[0]

    # calcul du point sur l'object en applicant la pseudo-inverse de la camera sur le point trouvé plus-haut

    leftObject = (np.linalg.pinv(camLeft) @ pL)
    rightObject = (np.linalg.pinv(camRight) @ pR)

    # conversion des np.array en mathutils.Vector pour l'utilisation de la methode d'intersection

    leftEndVec = arrayToVector(leftObject)
    rightEndVec = arrayToVector(rightObject)

    leftStartVec = arrayToVector(camCenterLeft)
    rightStartVec = arrayToVector(camCenterRight)

    # affichage des lignes reliant centre à point objet

    '''
    draw3DLine(camCenterLeft,leftObject)
    draw3DLine(camCenterRight,rightObject)
    plt.show()
    '''

    # utilisation de mathutils.geometry.intersect_line_line pour trouver l'intersection des lingnes passant par les 2
    # points.
    return pygeo.intersect_line_line(leftStartVec, leftEndVec, rightStartVec, rightEndVec)


def draw3DLine(start, end):
    figure = plt.figure()
    ax = Axes3D(figure)

    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')

    x_start, y_start, z_start = start
    x_end, y_end, z_end = end

    print("start = ({},{},{})".format(x_start, y_start, z_start))
    print("end = ({},{},{})\n".format(x_end, y_end, z_end))

    ax.scatter(x_start, y_start, z_start, c='r', marker='o')
    ax.plot([x_start, x_end], [y_start, y_end], [z_start, z_end])


def getObjectPoint():
    point = [[], [], []]
    for l in range(26):
        pointsLeft = np.array(epl[l][0])

        pointRight = np.array(pointsRight[l])
        for i in range(len(pointsLeft[0])):
            try:

                # calcul du point d'intersection sur l'objet -> on obtient une liste de vector
                intersection = getIntersection(pointsLeft[:, i], pointRight[:, i])
                # print(intersection)
                for inter in intersection:
                    inter *= 1000
                    x, y, z = inter
                    point[0].append(x)
                    point[1].append(y)
                    point[2].append(z)
            except:
                pass
    return np.array(point)


def drawPointObject(point):
    figure = plt.figure()
    ax = Axes3D(figure)

    ax.scatter3D(point[0, :], point[1, :], point[2, :], c='black', marker='x')

    ax.view_init(-95, -50)
    plt.axis('off')
    plt.show()


def drawSurfaceObject(point):
    figure = plt.figure()
    ax = Axes3D(figure)
    ax.plot_trisurf(point[0, :], point[1, :], point[2, :])

    ax.view_init(-95, -50)
    plt.axis('off')
    plt.show()


def pointToJson(point):
    data = {'x': point[0, :].tolist(), 'y': point[1, :].tolist(), 'z': point[2, :].tolist()}
    with open('point.txt', '+w') as file:
        json.dump(data, file)


point = getObjectPoint()
drawSurfaceObject(point)
drawPointObject(point)
pointToJson(point)
