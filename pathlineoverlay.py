import cv2
import numpy as np
import math

def draw_pathlines(image, roi):
    x, y, w, h = roi

    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(grayscale, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 200, None, 3)

    mask = np.zeros_like(edges)
    mask[y:y+h, x:x+w] = edges[y:y+h, x:x+w]

    #https://docs.opencv.org/4.x/d3/de6/tutorial_js_houghlines.html defines houghline parameters and returns
    lines = cv2.HoughLines(mask, 1, np.pi / 180, 200, None, 0, 0)
    detected_lines = []

    pathlines = []
    finalpath = []
    if lines is not None:
        for i in range(0, len(lines)):
            rho = lines[i][0][0] #extracting distance from origin in hough space
            theta = lines[i][0][1] # extracting angle
            detected_lines.append((rho, theta))

            matched = False
            for line in pathlines:
                #comparing slope to other lines in path lines to match
                if abs(rho - line[0]) < 20 and abs(theta - line[1]) < np.pi / 36:
                    #calculating line average between these two lines for singular path line
                    line[0] = (line[0] + rho) / 2
                    line[1] = (line[1] + theta) / 2
                    matched = True
                    break
            if not matched:
                pathlines.append([rho, theta])

        for center in pathlines:
            rho = center[0]
            theta = center[1]
            #going from polar to cartesian
            #https://www.khanacademy.org/computing/computer-programming/programming-natural-simulations/programming-angular-movement/a/polar-coordinates#:~:text=Another%20useful%20coordinate%20system%20known,y%20components%20of%20a%20vector
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            #extending lines / calculating endpoints
            pt1 = (int(x0 +1000 * (-b)), int(y0 +1000 * (a)))
            pt2 = (int(x0 -1000 * (-b)), int(y0 -1000 * (a)))
            
            finalpath.append((pt1, pt2))

        for pt1, pt2 in finalpath:
            cv2.line(image, pt1, pt2, (0, 255, 0), 2, cv2.LINE_AA)

    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
    return image, finalpath

def dist(pt1,pt2):
    return np.linalg.norm(np.array(pt1) - np.array(pt2))

def intersection(ept1_1,ept2_1,ept1_2,ept2_2):
    det = (ept1_1[0] - ept2_1[0]) * (ept1_2[1] - ept2_2[1]) - (ept1_1[1] - ept2_1[1]) * (ept1_2[0] - ept2_2[0])

    if det == 0:
        return None  # Lines are parallel

    x = ((ept1_1[0] * ept2_1[1] - ept1_1[1] * ept2_1[0]) * (ept1_2[0] - ept2_2[0]) - (ept1_1[0] - ept2_1[0]) * (ept1_2[0] * ept2_2[1] - ept1_2[1] * ept2_2[0])) / det
    y = ((ept1_1[0] * ept2_1[1] - ept1_1[1] * ept2_1[0]) * (ept1_2[1] - ept2_2[1]) - (ept1_1[1] - ept2_1[1]) * (ept1_2[0] * ept2_2[1] - ept1_2[1] * ept2_2[0])) / det

    return int(x), int(y)

def draw_centerline(image, ptpath):
    if len(ptpath) < 2:
        return image 

    # calculating midpoints for each corresponding point to create center line
    #https://stackoverflow.com/questions/49037902/how-to-interpolate-a-line-between-two-other-lines-in-python following this concept
    midpoints = []
    for i in range(0, len(ptpath) - 1, 2):
        pt1_1, pt2_1 = ptpath[i]
        pt1_2, pt2_2 = ptpath[i + 1]

        if dist(pt1_1,pt1_2)>dist(pt1_1, pt2_2):
            midpoint1 = intersection(pt1_1,pt2_1,pt1_2,pt2_2)
            midpoint2 = ((pt1_1[0] + pt2_2[0]) // 2, (pt1_1[1] + pt2_2[1]) // 2)
            #midpoint2 = ((pt2_1[0] + pt1_2[0]) // 2, (pt2_1[1] + pt1_2[1]) // 2)
        else:
            midpoint1 = ((pt1_1[0] + pt1_2[0]) // 2, (pt1_1[1] + pt1_2[1]) // 2)
            midpoint2 = ((pt2_1[0] + pt2_2[0]) // 2, (pt2_1[1] + pt2_2[1]) // 2)

        midpoints.append((midpoint1, midpoint2))

    for midpoint1, midpoint2 in midpoints:
        cv2.line(image, midpoint1, midpoint2, (0, 0, 255), 2, cv2.LINE_AA)

    return image

cap = cv2.VideoCapture(0)

roi = (300, 150, 600, 400)

while cap.isOpened():
    ret, frame = cap.read() 

    if not ret:
        print("Error, cannot recieve stream")
        break 
    
    pathframe, lines = draw_pathlines(frame, roi)
    overframe = draw_centerline(pathframe, lines)

    cv2.imshow('frame', overframe)

    if cv2.waitKey(1) == ord('q'):  
        break

cap.release()
cv2.destroyAllWindows()
