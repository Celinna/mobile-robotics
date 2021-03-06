# -*- coding: utf-8 -*-

import numpy as np
import cv2
import cv2.aruco as aruco
import unwarp
import math

aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)

def detect_thymio(img,pixel2mmx,pixel2mmy):
    """
    Detect the location and angle of the Thymio robot using Aruco markers
    Parameters:
        image (grayscale img): source image
        pixel2mmx (float): pixel to millimeter for x direction
        pixel2mmy (float): pixel to millimeter for y direction
    Returns:
        newPos (5x1 np.array): [x; y; angle (rad); 0; 0] corresponding to 
                current position of thymio
    """
    
    # Detect aruco markers
    corners, ids, rejectedImgPoints = aruco.detectMarkers(img, aruco_dict)
    corners = np.array(corners)
    
    Y,X = img.shape
    
    # initialize position
    newPos = np.zeros((5,1))
    
    # Plot identified markers, if any
    if ids is not None:
        # Draw location of aruco markers
        frame_markers = aruco.drawDetectedMarkers(img, corners, ids,borderColor = (0,0,255)) # convert back to RGBA
       
        #colorArr = cv2.cvtColor(color_rgb.copy(),cv2.COLOR_RGB2RGBA) # Converts images back to RGBA 

        pos = np.empty((len(ids),2))
        vec = np.empty((len(ids),2))
        
        c = corners[0][0] # Find center of marker
            
        pos = np.array([c[:,0].mean()*pixel2mmy,  (Y-c[:,1].mean())*pixel2mmx])
        pos = pos.astype(int)
        #print('Chair located at'+str(chair_x)+ " and " + str(chair_y))
        #print(c)
        vec = (c[1,:] + c[0,:])/2 - (c[2,:] + c[3,:])/2  # Find orientation vector of chair
        vec = vec/ np.linalg.norm(vec) # Convert to unit vector
        ang = math.atan2(vec[0], vec[1])
        
        newPos[0] = pos[0]
        newPos[1] = pos[1]
        newPos[2] = ang

    return newPos


def init_video(img, save_img):
    """
    Find the intial points of the map. Save the map image if needed. 
    Parameters:
        image (color img): source image 
        save_img (boolean): whether to save the image as .jpg
    Returns:
        gray (grayscale img): warped image
        pts (np.array): [x,y] coordinates of corners of unwarped image
        pixel2mmx (float): pixel to millimeter for x direction
        pixel2mmy (float): pixel to millimeter for y direction
    """
    pts = unwarp.get_corners(img) # will be used to unwarp all images from live feed
    
    warped = unwarp.four_point_transform(img, pts)
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    
    # Map size is 1188 x 840
    X,Y = gray.shape # X and Y are flipped here
    pixel2mmx = 840 / X
    pixel2mmy = 1188 / Y
    
    if save_img:
        # show and save the warped image
        cv2.imshow("Warped", warped)
        cv2.imwrite('map.jpg',warped)

    return warped, gray, pts, pixel2mmx, pixel2mmy


def match_template(img,template,plot):
    """
    Find the goal location based on template matching. Code retrieved from
    https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_template_matching/py_template_matching.html
    Parameters:
        image (color img): source image 
        plot (boolean): whether to plot rectangle over detected template
    Returns:
        goal (np.arra): [x,y] coordinates of goal
    """
    img_orig = img
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    w, h = template.shape[::-1]

    # All the 6 methods for comparison in a list
    # methods = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR',
    #             'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']
    meth = 'cv2.TM_SQDIFF_NORMED'
    
    method = eval(meth)
    # Apply template Matching
    res = cv2.matchTemplate(img,template,method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    
    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        top_left = min_loc
    else:
        top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)
    
    goal = np.array([(bottom_right[0]+top_left[0])/2,(bottom_right[1]+top_left[1])/2]).astype(int)
    # flip y-axis of goal to match existing coordinate system
    X,Y = img.shape
    goal[1] = X - goal[1]

    if plot:
        cv2.rectangle(img_orig,top_left, bottom_right, (0,255,0), 2) # Identify goal
    
    return goal, img_orig


# img = cv2.imread('get_goal.jpg')
# template = cv2.imread('template.jpg',0)
# goal = match_template(img,template,True)