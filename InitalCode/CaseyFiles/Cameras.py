import cv2
from picamera2 import Picamera2
from picamera2 import controls

def main():
    primaryCam = Picamera2(0)
    rearCam = Picamera2(1)
    clawCam = cv2.VideoCapture(16)

    primaryCam.configure(primaryCam.create_preview_configuration(main={"size": (1280,720)}))
    rearCam.configure(rearCam.create_preview_configuration(main={"size": (1280,720)}))
    clawCam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    clawCam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    primaryCam.start()
    rearCam.start()

    primaryCam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
    primaryCam.autofocus_cycle()

    active = 1

    while True:
        if active == 1:
            frame = primaryCam.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            name = "Primary Camera"
        elif active == 2:
            frame = rearCam.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            name = "Rear Camera"
        elif active == 3:
            ret, frame = clawCam.read()
            name = "Claw Camera"

        cv2.imshow(name, frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('1'):
            active = 1
            cv2.destroyAllWindows()
        elif key == ord('2'):
            active = 2
            cv2.destroyAllWindows()
        elif key == ord('3'):
            active = 3
            cv2.destroyAllWindows()
        elif key == ord('q'):
            break
        
    primaryCam.stop()
    rearCam.stop()
    clawCam.release()
    cv2.destroyAllWindows()

main()
