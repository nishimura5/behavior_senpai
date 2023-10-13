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
