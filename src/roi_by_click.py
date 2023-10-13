import cv2


def main(rcap):
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
