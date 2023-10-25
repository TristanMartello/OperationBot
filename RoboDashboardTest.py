import pygame
import paho.mqtt.client as mqtt
import math


broker_address = '10.243.39.227'
timerMax = 20

# Initialize screen dimensions and color constants
screenWidth = 650
screenHeight = 600

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LGRAY = (170, 170, 170)
MGRAY = (100, 100, 100)
DGRAY = (60, 60, 60)
RED = (255, 0, 0)
LRED = (246, 90, 90)

# Initialize Keypress dictionary and estimated motor positions
keyDict = {"w": False, "a": False, "s": False, "d": False, "^": False, "<": False, ">": False, "v": False, " ": False}
dropY = 290

# left, right, base, pivot
motorAngles = {"left": 0, "right": 0, "base": 0, "pivot": 0}

sendActive = False

# Screen drawing shell function
def drawScreen(screen):
    screen.fill([0, 0, 0])
    feedX, conX = drawHeader(screen)
    arrowKeys(screen, conX)
    motorDisplay(screen)
    drawIcon(screen)
    # dividers(screen)

# Draw the four motor gauges
def motorDisplay(screen):
    startX, startY = 100, 180
    posMod = [(0, 0), (150, 0), (0, 150), (150, 150)]
    i = 0
    for motor in motorAngles:
        drawMotor(screen, startX + posMod[i][0], startY + posMod[i][1], motorAngles[motor], motor.upper())
        i += 1

# For each motor icon, make the outer circle, word, and rotating position circle
def drawMotor(screen, centerX, centerY, theta, label):
    radius = 60
    pygame.draw.circle(screen, LGRAY, (centerX, centerY), radius, 10)
    xc = centerX + (radius * math.cos(toRad(theta)))
    yc = centerY - (radius * math.sin(toRad(theta)))
    pygame.draw.circle(screen, RED, (xc, yc), 10)
    textCenter = centerText(label, centerX, 30)
    displayText(screen, 30, label, WHITE, (textCenter, centerY - 10))

def toRad(deg):
    return deg * math.pi / 180

# Draw the mini icon of our robot
def drawIcon(screen):
    centerX = int(screenWidth / 4)
    startY = 480
    iconColor = LRED
    # Car body and stabilizer
    pygame.draw.rect(screen, iconColor, (centerX - 50, startY, 70, 15), 0)
    pygame.draw.circle(screen, iconColor, (centerX - 40, startY + 18), 6)
    # Arm joints
    pygame.draw.polygon(screen, iconColor, [(centerX - 10, startY), (centerX + 10, startY - 30),
                                            (centerX + 25, startY - 30), (centerX + 5, startY)])
    pygame.draw.polygon(screen, iconColor, [(centerX + 15, startY - 28), (centerX + 50, startY - 10),
                                            (centerX + 65, startY - 10), (centerX + 25, startY - 30)])
    # Border
    pygame.draw.circle(screen, iconColor, (centerX + 6, startY), 75, 5)

    # For each motor icon, change the color if motor is being activated
    # Front wheel
    pygame.draw.circle(screen, getItemColor("wheel"), (centerX + 3, startY + 18), 9)
    # Arm base
    pygame.draw.circle(screen, getItemColor("base"), (centerX, startY - 3), 7)
    # Arm pivot
    pygame.draw.circle(screen, getItemColor("pivot"), (centerX + 18, startY - 28), 8)
    # Bucket
    pygame.draw.rect(screen, getItemColor("bucket"), (centerX + 52, startY - 10, 15, 15), 0)

# Determine if each motor is being activated based on the key press dictionary
def getItemColor(name):
    codeDict = {"wheel": ["w", "a", "s", "d"], "base": ["<", ">"], "pivot": ["^", "v"], "bucket": [" "]}
    fin = False
    for code in codeDict[name]:
        fin = fin or keyDict[code]
    if fin:
        return WHITE
    else:
        return LRED

# Draw the keyboard display
def arrowKeys(screen, conX):
    keySide = 60
    centerX = conX + 55
    # ASDW for driving
    drawFourKeys(screen, centerX=conX+55, startY=140, keySide=keySide, word="DRIVE", syms=["w", "a", "d", "s"])
    # Four arrow keys for the arm
    drawFourKeys(screen, centerX=conX+55, startY=390, keySide=keySide, word="ARM", syms=["^", "<", ">", "v"])
    drawDropButt(screen, centerX)

# Debugging function for drawing center lines to help with positioning
def dividers(screen):
    pygame.draw.line(screen, WHITE, (screenWidth / 2, 0), (screenWidth / 2, screenHeight), 1)
    pygame.draw.line(screen, WHITE, (screenWidth / 4, 0), (screenWidth / 4, screenHeight), 1)
    pygame.draw.line(screen, WHITE, (3 * screenWidth / 4, 0), (3 * screenWidth / 4, screenHeight), 1)

# Draws four keys centered around a specified point, tracks color changes with the key press dictionary
def drawFourKeys(screen, centerX, startY, keySide, word, syms):
    wordX = centerText(word, centerX, 25)
    displayText(screen, 20, word, WHITE, (wordX, startY + 45))
    xList = [0, -70, 70, 0]
    yList = [0, 50, 50, 100]
    for (x, y, sym) in zip(xList, yList, syms):
        if keyDict[sym]:
            back = DGRAY
            text = WHITE
        else:
            back = LGRAY
            text = BLACK
        drawSquare(screen, (centerX + x, startY + y), keySide, back)
        displayText(screen, 25, sym, text, (centerX + x - 5, startY + y - 10))

# Draws the bucket drop button
def drawDropButt(screen, centerX):
    global dropX
    if not keyDict[" "]:
        dropColor = RED
        textColor = BLACK
    else:
        dropColor = MGRAY
        textColor = WHITE
    dropX = centerX - 50
    pygame.draw.rect(screen, dropColor, (centerX - 50, dropY, 100, 50), 0, border_radius=10)
    dropCenX = centerText("DROP", centerX, 30)
    displayText(screen, 30, "DROP", textColor, (dropCenX - 5, dropY + 15))

# Handles mouse position to see if the user is clicking on the drop button
def checkDropBounds(x, y):
    return (x >= dropX) and (x <= dropX + 100) and (y >= dropY) and (y <= dropY + 50)

# Simple draw square function based on center position and side length
def drawSquare(screen, center, side, color):
    pygame.draw.rect(screen, color, (center[0] - (side / 2), center[1] - (side / 2), side, side), 0, border_radius=10)

# Draw the big text labels
def drawHeader(screen):
    y1 = 15
    y2 = y1 + 40
    y3 = y2 + 25

    title = "DASHBOARD"
    titleCenter = centerText(title, screenWidth / 2, 50)
    displayText(screen, 50, "DASHBOARD", WHITE, (titleCenter, y1))
    pygame.draw.line(screen, WHITE, (0, y2), (screenWidth, y2), 3)

    feedX = centerText("FEEDBACK", screenWidth / 4, 30) - 20
    displayText(screen, 30, "FEEDBACK", WHITE, (feedX + 30, y3))

    conX = centerText("CONTROL", 3*screenWidth / 4, 30) + 20
    displayText(screen, 30, "CONTROL", WHITE, (conX, y3))
    return feedX, conX

# Returns the 'starting' x value based on the of a word, its font size, and where it should be centered
def centerText(text, centerX, fontSize):
    letterWidth = (fontSize / 2) - 2
    return centerX - ((len(text) * letterWidth) / 2)

# Displays text on the screen
def displayText(screen, fontSize, text, color, coords):
    font = pygame.font.SysFont(None, fontSize)
    img = font.render(text, True, color)
    screen.blit(img, coords)

# Callback mqtt function, not used in this program
def callback(source, user, message):
    print("received ", str(message.payload.decode("utf-8")))
    print("from topic ", message.topic)

# Initializes communication with the broker
def startClient():
    global client
    client = mqtt.Client("tristan")
    client.on_message = callback

    client.connect(broker_address)
    client.loop_start()
    return client

# Handles key presses and releases, and updates the arm status, drive status, and key press dictionary
def processKey(retBool, key, armStatus, driveStatus):
    armDict = {pygame.K_LEFT: ["left", "<"], pygame.K_RIGHT: ["right", ">"], pygame.K_UP: ["up", "^"], pygame.K_DOWN: ["down", "v"]}
    carDict = {pygame.K_w: ["reverse", "w"], pygame.K_a: ["left", "a"], pygame.K_s: ["forward", "s"], pygame.K_d: ["right",
                                                                                                                   "d"]}
    if key in armDict.keys():
        if retBool:
            armStatus = armDict[key][0]
        else:
            armStatus = "halt"
        keyDict[armDict[key][1]] = retBool
        print(armStatus)

    elif key in carDict.keys():
        if retBool:
            driveStatus = carDict[key][0]
        else:
            driveStatus = "halt"
        keyDict[carDict[key][1]] = retBool
        print(driveStatus)

    elif key == pygame.K_SPACE:
        if sendActive:
            client.publish('drop', 'drop')
        keyDict[" "] = retBool

    else:
        return True, armStatus, driveStatus

    return False, armStatus, driveStatus

# Uses the key press dictionary to create the graphic motion of the motor gauges
def updateAngles(armStatus, driveStatus):
    inc = 1
    driveMods = {"forward": [inc, inc], "reverse": [-inc, -inc], "left": [-inc, inc], "right": [inc, -inc]}
    armMods = {"up": [0, inc], "down": [0, -inc], "left": [inc, 0], "right": [-inc, 0]}

    if driveStatus != "halt":
        motorAngles["left"] = (motorAngles["left"] + driveMods[driveStatus][0]) % 360
        motorAngles["right"] = (motorAngles["right"] + driveMods[driveStatus][1]) % 360

    if armStatus != "halt":
        print(armStatus)
        motorAngles["base"] = (motorAngles["base"] + armMods[armStatus][0]) % 360
        motorAngles["pivot"] = (motorAngles["pivot"] + armMods[armStatus][1]) % 360

# Overall main function
def main():
    if sendActive:
        client = startClient()
    pygame.init()
    # Set up the drawing window
    screen = pygame.display.set_mode([screenWidth, screenHeight])  # [width, height]

    armStatus = "halt"
    driveStatus = "halt"

    timer = timerMax
    run = True
    # Pygame events track key presses, releases, and mouse clicks, which control mqtt message sending
    # This loop updates many times a second, and creates smooth animations with screen updates
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                unknown, armStatus, driveStatus = processKey(True, event.key, armStatus, driveStatus)
                if unknown:
                    print("Unknown key press")
            elif event.type == pygame.KEYUP:
                unknown, armStatus, driveStatus = processKey(False, event.key, armStatus, driveStatus)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]
                if checkDropBounds(x, y):
                    if sendActive:
                        client.publish('drop', 'drop')
                    keyDict[" "] = True
            elif event.type == pygame.MOUSEBUTTONUP:
                x, y = pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]
                if checkDropBounds(x, y):
                    keyDict[" "] = False

        # Update angle visuals and draw the updated screen
        updateAngles(armStatus, driveStatus)
        drawScreen(screen)
        pygame.display.flip()

        # If not in graphic debugging mode, send the pico the latest arm and drive updates
        if sendActive:
            if timer == 0:
                client.publish('arm', armStatus)
                client.publish('drive', driveStatus)
                timer = timerMax
            else:
                timer -= 1

    pygame.quit()


main()
