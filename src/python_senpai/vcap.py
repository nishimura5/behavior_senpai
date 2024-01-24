import cv2
import numpy as np


class VideoCap(cv2.VideoCapture):
    def __init__(self):
        super().__init__()
        self.frame_size = (0, 0)
        self.max_msec = 0

    def open_file(self, file_path):
        """
        動画ファイルを開く
        initで開くとsegfaultの原因になるため、open_file()を使う
        """
        ok = self.open(file_path, apiPreference=cv2.CAP_ANY, params=[cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY])
        if ok is False:
            print(f"Failed to open {file_path}")

    def read_at(self, msec, scale=None, rgb=False):
        '''
        ミリ秒を指定してreadする
        '''
        self.set(cv2.CAP_PROP_POS_MSEC, msec)
        ok, frame = self.read()
        if ok is True and rgb is True:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if scale is not None:
            frame = cv2.resize(frame, None, fx=scale, fy=scale)
        return ok, frame

    def read_anyway(self):
        '''
        readに失敗したら黒画像を返す
        '''
        ok, frame = self.read()
        if ok is False:
            frame = np.zeros((self.frame_size[1], self.frame_size[0], 3), dtype=np.uint8)
        return frame

    def get_frame_size(self):
        return self.frame_size

    def set_frame_size(self, frame_size):
        '''
        read_anyway()を見越してフレームのwidthとheightをsetする(resizeはしない)
        '''
        self.frame_size = frame_size

    def set_max_msec(self, max_msec):
        self.max_msec = max_msec

    def get_max_msec(self):
        return self.max_msec


class MultiVcap():
    '''
    分割されたmp4に対して、通しのmsecでread_atするためのクラス
    '''
    def __init__(self):
        self.vcaps = []

    def open_files(self, file_path_list, total_msec_list):
        # file_path_listとtotal_msec_listは先頭が最初の動画になっていること
        self.total_msec_list = total_msec_list
        for file_path in file_path_list:
            vc = VideoCap()
            vc.open_file(file_path)
            self.vcaps.append(vc)

    def read_at(self, msec):
        '''
        ミリ秒を指定してreadする
        '''
        tar_idx = 0
        for tar_msec in self.total_msec_list:
            if msec <= tar_msec:
                break
            tar_idx += 1

        tar_vcap = self.vcaps[tar_idx]
        if tar_idx == 0:
            ok, frame = tar_vcap.read_at(msec)
        else:
            tar_msec = msec - self.total_msec_list[tar_idx-1]
            ok, frame = tar_vcap.read_at(tar_msec)
        return ok, frame

    def clear(self):
        self.vcaps = []


class RoiCap(cv2.VideoCapture):
    def __init__(self):
        super().__init__()

    def open_file(self, file_path):
        """
        動画ファイルを開く
        initで開くとsegfaultの原因になるため、open_file()を使う
        """
        ok = self.open(file_path, apiPreference=cv2.CAP_ANY, params=[cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY])
        if ok is False:
            print(f"Failed to open {file_path}.")

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

    def get_left_top(self):
        return self.left_top_point

    def get_roi_frame(self):
        '''
        read()と互換
        '''
        ok, frame = self.read()
        if ok is True:
            frame = frame[self.left_top_point[1]:self.right_bottom_point[1], self.left_top_point[0]:self.right_bottom_point[0]]
        return ok, frame

    def click_roi(self):
        '''
        imshow()を使ったGUIでROIを指定
        '''
        ret, frame = self.read()
        src_img = frame.copy()
        cv2.namedWindow("frame", cv2.WINDOW_NORMAL)
        cv2.imshow("frame", src_img)
        cv2.setMouseCallback("frame", self.mouse_callback)

        left_top_circle_pos = (0, 0)
        right_bottom_circle_pos = (self.width, self.height)

        self.left_top_point = left_top_circle_pos
        self.right_bottom_point = right_bottom_circle_pos

        while True:
            cv2.imshow("frame", src_img)
            if self.left_top_point != left_top_circle_pos or self.right_bottom_point != right_bottom_circle_pos:
                src_img = frame.copy()
                cv2.rectangle(src_img, self.left_top_point, self.right_bottom_point, (0, 255, 0), 2)
                left_top_circle_pos = self.left_top_point
                right_bottom_circle_pos = self.right_bottom_point

            # xを押すとキャンセル、スペースを押すと確定
            key = cv2.waitKey(1) & 0xFF
            if key == ord('x'):
                self.left_top_point = (0, 0)
                self.right_bottom_point = (self.width, self.height)
                break
            if key == ord(' '):
                break
        cv2.destroyAllWindows()
        self.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.set_roi(self.left_top_point, self.right_bottom_point)

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.left_top_point = (x, y)
        if event == cv2.EVENT_RBUTTONDOWN:
            self.right_bottom_point = (x, y)
