import cv2
import time
import tkinter
import numpy as np
# import HandTracking as htm
import mediapipe as mp
import pynput.mouse as Mouse
import pynput.keyboard as Keyboard

from flask import Flask, render_template, Response

app = Flask(__name__)

# Get resolution of the Monitor Screen
root = tkinter.Tk()
width = root.winfo_screenwidth()
height = root.winfo_screenheight()

# Mouse and Keyboard Instance
mouse = Mouse.Controller()
keyboard = Keyboard.Controller()

# Video Camera Screen Dimension
wCam, hCam = 640, 480

# Frame Reduction
frameR = 125  # Mouse Use Box

# Taking the input from primary camera
# Storing the feed in a variable
cap = cv2.VideoCapture(0)

# Setting the dimension of the captured feed
cap.set(3, wCam)
cap.set(4, hCam)

# Hand Detector Module
# 50% Confidence hand detected
mpHands = mp.solutions.hands
hands = mpHands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5,
                      min_tracking_confidence=0.5)
mpDraw = mp.solutions.drawing_utils
results = None

# Initialise binary variables
is_present = 0
pinky_up = 0
thumb_up = 0
index_up = 0
key_pressed = 0
mouse_pressed = 0
erased = 0

# Initialise time variables
next_time = 0
previous_time = 0
pressed_start = 0
txt_time = 16
disp_time = 0

# Initialise lists
present_distances = []
tipIds = [4, 8, 12, 16, 20]
lmList = []

# String
txt = 0
disp = ''


# Scale Hand for Depth
def scale(lmList):
    sq_x = 0
    sq_y = 0
    for i in [1, 5, 9, 13, 17]:
        sq_x = sq_x + (lmList[i][1] - lmList[0][1]) ** 2
        sq_y = sq_y + (lmList[i][2] - lmList[0][2]) ** 2
    size = int(np.sqrt(sq_x + sq_y))
    zoom = 1 / (size / 300)
    return zoom


# Function to get distance of fingers from thumb
def distance(lmList):
    # Global Variables
    global present_distances

    # Calling Scale Function
    zoom = scale(lmList)

    # Coordinates of fingers
    thumb1, thumb2 = lmList[4][1], lmList[4][2]
    index1, index2 = lmList[8][1], lmList[8][2]
    middle1, middle2 = lmList[12][1], lmList[12][2]
    ring1, ring2 = lmList[16][1], lmList[16][2]
    pinky1, pinky2 = lmList[20][1], lmList[20][2]

    # Distance of fingers from thumb
    hyp = np.sqrt((index1 - thumb1) ** 2 + (index2 - thumb2) ** 2
                  + (middle1 - thumb1) ** 2 + (middle2 - thumb2) ** 2
                  + (ring1 - thumb1) ** 2 + (ring2 - thumb2) ** 2
                  + (pinky1 - thumb1) ** 2 + (pinky2 - thumb2) ** 2)

    # Adjusting distance for depth
    hyp = hyp * zoom

    # Appending Distances
    present_distances.append(hyp)


# Presentation Mode On
def present_on(lmList):
    # Global Variables
    global is_present, present_distances, txt

    # Call Distance Function
    distance(lmList)

    # Press F5 on gesture
    try:
        if is_present == 0:
            if present_distances[-6] < 150:
                nxt = present_distances[-6]
                for i in present_distances[-5:-1]:
                    if i > nxt:
                        nxt = i
                    else:
                        break

                if nxt > 360:
                    txt = 'Present'
                    keyboard.press(Keyboard.Key.f5)
                    keyboard.release(Keyboard.Key.f5)
                    is_present = 1
    except:
        pass


# Presentation Mode Off
def present_off():
    # Global Variables
    global is_present, present_distances, txt

    try:
        if is_present == 1:
            nxt = 0
            if present_distances[-6] > 360:
                nxt = present_distances[-6]
                for i in present_distances[-5:-1]:
                    if i < nxt:
                        # print(next)
                        nxt = i
                    else:
                        break

                if nxt < 150:
                    txt = 'Leave Presentation Mode'
                    keyboard.press(Keyboard.Key.esc)
                    keyboard.release(Keyboard.Key.esc)
                    keyboard.press(Keyboard.Key.esc)
                    keyboard.release(Keyboard.Key.esc)
                    is_present = 0
    except:
        pass


# Fingers Up or Down
def fingers_up(lmList):
    # Global Variable
    global tipIds

    # Local Variable
    fingers = []

    if lmList[tipIds[0]][1] < lmList[tipIds[0] - 1][1]:
        fingers.append(1)
    else:
        fingers.append(0)

    for id in tipIds[1:]:
        if lmList[id][2] < lmList[id - 2][2]:
            fingers.append(1)
        else:
            fingers.append(0)

    return fingers


# Thumbs Up or Down
def thumbs_up(lmList):
    # Global Variable
    global tipIds

    # Local Variable
    fingers = []

    if lmList[tipIds[0]][2] < lmList[tipIds[0] - 2][2]:
        fingers.append(1)
    else:
        fingers.append(0)

    for id in tipIds[1:]:
        if lmList[id][1] < lmList[id - 2][1]:
            fingers.append(1)
        else:
            fingers.append(0)

    return fingers


# Next Slide
def next_slide(lmList):
    # Global Variable
    global pinky_up, next_time, tipIds, txt

    # Local Variable
    fingers = fingers_up(lmList)

    # Only pinky up
    if (fingers[4] == 1) & (fingers[3] == 0) & (fingers[0] == 0):
        if pinky_up == 0:
            pinky_up = 1
            txt = 'Next Slide'
            keyboard.press('n')
            keyboard.release('n')
            next_time = time.time()

    if (time.time() - next_time) >= 2 and pinky_up == 1:
        pinky_up = 0


# Previous Slide
def previous_slide(lmList):
    # Global Variable
    global thumb_up, previous_time, tipIds, txt

    # Local Variable
    fingers = thumbs_up(lmList)

    # Only thumbs up
    if (fingers[2] == 0) & (fingers[1] == 0) & (fingers[3] == 0) & (fingers[4] == 0) & (fingers[0] == 1) & (
            lmList[4][2] < 225):
        if thumb_up == 0:
            thumb_up = 1
            txt = 'Previous Slide'
            keyboard.press('p')
            keyboard.release('p')
            previous_time = time.time()

    if (time.time() - previous_time) >= 2 and thumb_up == 1:
        thumb_up = 0


# Index UP
def cursor_move(lmList, img):
    # Global Variable
    global index_up, frameR, width, height, txt

    # Local Variable
    fingers = fingers_up(lmList)
    x1, y1 = lmList[8][1], lmList[8][2]

    if (fingers[1] == 1) & (fingers[2] == 0):
        if index_up == 0:
            txt = 'Cursor Active'
            index_up = 1
        cv2.circle(img, (x1, y1), 8, (255, 0, 255), cv2.FILLED)

        # Convert Coordinates
        x3 = np.interp(x1, (frameR, cap.get(3) - frameR), (0, width))
        y3 = np.interp(y1, (frameR, cap.get(4) - frameR), (0, height))
        mouse.position = (x3, y3)

    else:
        index_up = 0


# Index and Middle Raised
def cursor_hold(lmList, img):
    # Global Variable
    global frameR, width, height, mouse_pressed, key_pressed, erased, pressed_start, txt

    x1, y1 = lmList[8][1], lmList[8][2]
    x2, y2 = lmList[12][1], lmList[12][2]

    fingers = fingers_up(lmList)
    zoom = scale(lmList)
    dist = np.sqrt((lmList[8][1] - lmList[12][1]) ** 2 + (lmList[8][2] - lmList[12][2]) ** 2)
    dist = dist * zoom

    # Index and Middle raised : Click
    if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0:
        cv2.line(img, (lmList[8][1], lmList[8][2]), (lmList[12][1], lmList[12][2]), (255, 0, 0), 3)

        if dist < 45:
            cv2.circle(img, (x1, y1), 8, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 8, (255, 0, 255), cv2.FILLED)
            x3 = np.interp(x1, (frameR, cap.get(3) - frameR), (0, width))
            y3 = np.interp(y1, (frameR, cap.get(4) - frameR), (0, height))
            if mouse_pressed == 1:
                mouse.position = (x3, y3)
                mouse.press(Mouse.Button.left)

            if key_pressed == 0:
                with keyboard.pressed(Keyboard.Key.ctrl):
                    keyboard.press('p')
                    keyboard.release('p')
                key_pressed = 1
                mouse_pressed = 1
                erased = 0
                pressed_start = time.time()
                txt = 'Drawing Mode On'

        if (mouse_pressed == 1) & ((time.time() - pressed_start) > 11):
            mouse.release(Mouse.Button.left)
            mouse_pressed = 0
            txt = 'Drawing Mode Off'

        if dist > 50:
            if key_pressed == 1:
                if mouse_pressed == 1:
                    mouse.release(Mouse.Button.left)
                    mouse_pressed = 0
                key_pressed = 0
                with keyboard.pressed(Keyboard.Key.ctrl):
                    keyboard.press('a')
                    keyboard.release('a')
                txt = 'Drawing Mode Off'


# Erase
def erase_draw(lmList):
    # Global Variable
    global erased, txt

    fingers = fingers_up(lmList)

    if (fingers == [1, 1, 1, 1, 1]) & (erased == 0):
        txt = 'Erase'
        keyboard.press('e')
        keyboard.release('e')
        erased = 1


# Find Hands
def findHands(img, draw=True):
    global hands, mpHands, results, mpDraw
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)
    # print(results.multi_hand_landmarks)
    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            if draw:
                mpDraw.draw_landmarks(img, handLms,
                                           mpHands.HAND_CONNECTIONS)
    return img


# Hands Position
def findPosition(img, handNo=0, draw=True):
    global myHand, results
    lmList = []
    if results.multi_hand_landmarks:
        myHand = results.multi_hand_landmarks[handNo]
        for id, lm in enumerate(myHand.landmark):
            # print(id, lm)
            h, w, c = img.shape
            cx, cy = int(lm.x * w), int(lm.y * h)
            # print(id, cx, cy)
            lmList.append([id, cx, cy])
            if draw:
                cv2.circle(img, (cx, cy), 7, (255, 0, 255), cv2.FILLED)
    return lmList


# Main
def generate_frames():
    global txt_time, txt, disp_time, disp
    while True:
        success, img = cap.read()
        if not success:
            break
        img = cv2.flip(img, 1)
        img = findHands(img)
        lmList = findPosition(img, draw=False)
        txt = 0
        txt_time = txt_time + 1

        if len(lmList) != 0:
            present_on(lmList)
            present_off()
            next_slide(lmList)
            previous_slide(lmList)
            cursor_move(lmList, img)
            cursor_hold(lmList, img)
            erase_draw(lmList)

        if txt_time > 1000:
            txt_time = 16
            disp_time = 0

        if txt != 0:
            disp = txt
            disp_time = txt_time

        if disp_time >= (txt_time - 15):
            cv2.putText(img, disp, (30, 30), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)

        ret, buffer = cv2.imencode('.jpg', img)
        img = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + img + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run(debug=True)
