import os

import cv2


class RoiCap(cv2.VideoCapture):
    def __init__(self, video_path):
        if os.path.exists(video_path) is False:
            raise FileNotFoundError(f"video_path:{video_path}")
        # cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY
        # を指定するとdecodeがGPUになる
        super().__init__(
            video_path,
            apiPreference=cv2.CAP_ANY,
            params=[cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY])
 
        self.width = int(self.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.left_top_point = (0, 0)
        self.right_bottom_point = (self.width, self.height)
        self.roi_width = self.right_bottom_point[0] - self.left_top_point[0]
        self.roi_height = self.right_bottom_point[1] - self.left_top_point[1]

    def set_roi(self, left_top_point, right_bottom_point):
        self.left_top_point = left_top_point
        self.right_bottom_point = right_bottom_point
        self.roi_width = right_bottom_point[0] - left_top_point[0]
        self.roi_height = right_bottom_point[1] - left_top_point[1]

    def get_roi_frame(self):
        ok, frame = self.read()
        if ok is True:
            frame = frame[self.left_top_point[1]:self.right_bottom_point[1], self.left_top_point[0]:self.right_bottom_point[0]]
        return ok, frame


def click_roi(rcap):
    ret, frame = rcap.read()
    src_img = frame.copy()
    cv2.imshow("frame", src_img)
    cv2.setMouseCallback("frame", mouse_callback)

    left_top_circle_pos = (0, 0)
    right_bottom_circle_pos = (rcap.width, rcap.height)

    global left_top_point, right_bottom_point
    left_top_point = left_top_circle_pos
    right_bottom_point = right_bottom_circle_pos

    while True:
        cv2.imshow("frame", src_img)
        if left_top_point != left_top_circle_pos or right_bottom_point != right_bottom_circle_pos:
            src_img = frame.copy()
            cv2.rectangle(src_img, left_top_point, right_bottom_point, (0, 255, 0), 2)
            left_top_circle_pos = left_top_point
            right_bottom_circle_pos = right_bottom_point

        # xを押すとキャンセル、スペースを押すと確定
        key = cv2.waitKey(1) & 0xFF
        if key == ord('x'):
            left_top_point = (0, 0)
            right_bottom_point = (rcap.width, rcap.height)
            break
        if key == ord(' '):
            break
    cv2.destroyAllWindows()
    rcap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    rcap.set_roi(left_top_point, right_bottom_point)


def mouse_callback(event, x, y, flags, param):
    global left_top_point, right_bottom_point
    if event == cv2.EVENT_LBUTTONDOWN:
        left_top_point = (x, y)
    if event == cv2.EVENT_RBUTTONDOWN:
        right_bottom_point = (x, y)
