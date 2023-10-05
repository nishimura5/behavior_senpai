import cv2
import mediapipe as mp
import pandas as pd

cap = cv2.VideoCapture("cup.mp4")
mp_holistic = mp.solutions.holistic.Holistic(model_complexity=2, refine_face_landmarks=True)

total_frame_num = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

mp_drawing = mp.solutions.drawing_utils
mph = mp.solutions.holistic
fps = cap.get(cv2.CAP_PROP_FPS)
out = cv2.VideoWriter('output.mp4', cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), fps, (frame_width*2, frame_height*2))

number_of_keypoints = {'face': 468, 'right_hand': 21, 'left_hand': 21}
# データの初期化
data_dict = {"frame": [], "member": [], "keypoint": [], "x": [], "y": [], "z": [], "timestamp": []}
for i in range(total_frame_num):
    ret, frame = cap.read()
    rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = mp_holistic.process(rgb_img)

    anno_img = cv2.resize(frame, (frame_width*2, frame_height*2), interpolation=cv2.INTER_CUBIC)
    mp_drawing.draw_landmarks(
        anno_img,
        results.face_landmarks,
        mph.FACEMESH_TESSELATION,
        mp_drawing.DrawingSpec(color=(250, 0, 40), thickness=1, circle_radius=1),
        mp_drawing.DrawingSpec(color=(200, 200, 200), thickness=1, circle_radius=0)
        )
    mp_drawing.draw_landmarks(
        anno_img,
        results.left_hand_landmarks,
        mph.HAND_CONNECTIONS,
        mp_drawing.DrawingSpec(color=(40, 40, 180), thickness=1, circle_radius=3),
        mp_drawing.DrawingSpec(color=(150, 150, 121), thickness=1, circle_radius=0)
        )
    mp_drawing.draw_landmarks(
        anno_img,
        results.right_hand_landmarks,
        mph.HAND_CONNECTIONS,
        mp_drawing.DrawingSpec(color=(40, 180, 40), thickness=1, circle_radius=3),
        mp_drawing.DrawingSpec(color=(150, 150, 121), thickness=1, circle_radius=0)
        )
    out.write(anno_img)

    timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)

    # 検出結果の取り出し
    member_ids = ['face', 'right_hand', 'left_hand']
    for member_id in member_ids:
        keypoints = getattr(results, f'{member_id}_landmarks').landmark
        if keypoints is None:
            continue
        for k in range(number_of_keypoints[member_id]):
            keypoint_id = k
            x = float(keypoints[k].x * frame_width)
            y = float(keypoints[k].y * frame_height)
            z = float(keypoints[k].z * frame_width)

            # データの詰め込み
            data_dict["frame"].append(i)
            data_dict["member"].append(member_id)
            data_dict["keypoint"].append(keypoint_id)
            data_dict["x"].append(x)
            data_dict["y"].append(y)
            data_dict["z"].append(z)
            data_dict["timestamp"].append(timestamp)

dst_df = pd.DataFrame(data_dict).set_index(["frame", "member", "keypoint"])
print(dst_df)
dst_df.to_csv("dst.csv")
