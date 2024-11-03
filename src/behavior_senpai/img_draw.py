import cv2


def mosaic(src_img, center, size, dilate=50):
    x, y = center
    size = int(size / 2)
    top = y - size - dilate
    bottom = y + size + dilate
    left = x - size - dilate
    right = x + size + dilate
    if top < 0:
        top = 0
    if bottom > src_img.shape[0]:
        bottom = src_img.shape[0]
    if left < 0:
        left = 0
    if right > src_img.shape[1]:
        right = src_img.shape[1]
    mos_width = right - left
    mos_height = bottom - top

    # 一度縮小して拡大することでモザイクをかける
    small = cv2.resize(src_img[top:bottom, left:right], None, fx=0.05, fy=0.05, interpolation=cv2.INTER_NEAREST)
    src_img[top:bottom, left:right] = cv2.resize(small, (mos_width, mos_height), interpolation=cv2.INTER_NEAREST)
    return src_img


def put_frame_pos(src_img, pos, total_frame_num, font_size=2):
    txt_font = cv2.FONT_HERSHEY_PLAIN
    text_pos = (10, font_size * 15)
    thickness = 2
    cv2.putText(src_img, f"{pos}/{total_frame_num}", text_pos, txt_font, font_size, (0, 0, 0), thickness * 3)
    cv2.putText(src_img, f"{pos}/{total_frame_num}", text_pos, txt_font, font_size, (255, 255, 255), thickness)


def put_message(src_img, message, font_size=2, y=30):
    txt_font = cv2.FONT_HERSHEY_PLAIN
    text_pos = (10, int(y))
    thickness = 2
    cv2.putText(src_img, message, text_pos, txt_font, font_size, (0, 0, 0), thickness * 3)
    cv2.putText(src_img, message, text_pos, txt_font, font_size, (255, 255, 255), thickness)


def draw_line(tar_img, start, end, color, thickness):
    if (start[0] == 0 and start[1] == 0) or (end[0] == 0 and end[1] == 0):
        return
    cv2.line(tar_img, start, end, color, thickness, cv2.LINE_AA)
