import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np

import test_rtmpose_pipeline as pipeline_tests
from test_rtmpose_pipeline import load_module

from behavior_senpai.bbox_iou_tracker import BBoxIoUTracker


class BBoxIoUTrackerTests(unittest.TestCase):
    def test_ids_follow_boxes_when_detection_order_changes(self):
        tracker = BBoxIoUTracker()
        np.testing.assert_array_equal(tracker.update([[0, 0, 10, 10], [100, 0, 110, 10]], 0), [0, 1])
        np.testing.assert_array_equal(tracker.update([[101, 0, 111, 10], [1, 0, 11, 10]], 1), [1, 0])

    def test_track_can_only_match_one_detection(self):
        tracker = BBoxIoUTracker()
        tracker.update([[0, 0, 10, 10]], 0)
        ids = tracker.update([[0, 0, 10, 10], [1, 0, 11, 10]], 1)
        np.testing.assert_array_equal(ids, [0, 1])

    def test_missing_frames_retention_and_expiration(self):
        tracker = BBoxIoUTracker(max_age=1)
        box = [[0, 0, 10, 10]]
        tracker.update(box, 0)
        self.assertEqual(tracker.update([], 1).shape, (0,))
        np.testing.assert_array_equal(tracker.update(box, 2), [0])
        tracker.update([], 3)
        tracker.update([], 4)
        np.testing.assert_array_equal(tracker.update(box, 5), [1])

    def test_new_location_and_new_video(self):
        tracker = BBoxIoUTracker(max_age=0)
        tracker.update([[0, 0, 10, 10]], 0)
        np.testing.assert_array_equal(tracker.update([[100, 0, 110, 10]], 1), [1])
        np.testing.assert_array_equal(tracker.update([[100, 0, 110, 10]], 0), [0])
        self.assertEqual(len(tracker.tracks), 1)

    def test_zero_area_iou_and_options(self):
        np.testing.assert_array_equal(BBoxIoUTracker._iou(np.zeros((1, 4)), np.zeros((1, 4))), [[0]])
        for options in [{"iou_threshold": 0}, {"iou_threshold": 1.1}, {"max_age": -1}, {"max_age": 1.5}]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                BBoxIoUTracker(**options)


class HandPipelineTests(unittest.TestCase):
    def setUp(self):
        self.apis = MagicMock()
        self.registry = MagicMock()
        self.processor_module = load_module("pose_video_processor", {
            "mmpose.registry": self.registry,
            "mmpose.structures": MagicMock(),
        })
        self.estimator_module = load_module("rtmpose_estimator", {"mmpose.apis": self.apis})
        self.module = load_module("rtmpose_hand_detector", {
            "mmdet.apis": self.apis,
            "mmdet.utils": MagicMock(),
            "mmengine.registry": MagicMock(),
            "behavior_senpai.pose_video_processor": self.processor_module,
            "behavior_senpai.rtmpose_estimator": self.estimator_module,
        })

    def detection(self, boxes, scores=None, labels=None):
        count = len(boxes)
        prediction = SimpleNamespace(
            bboxes=np.array(boxes, dtype=float).reshape(-1, 4),
            scores=np.array(scores if scores is not None else [0.9] * count),
            labels=np.array(labels if labels is not None else [0] * count),
        )
        self.apis.inference_detector.return_value.pred_instances.cpu.return_value.numpy.return_value = prediction

    def test_hand_filtering_bgr_input_tracking_and_empty_frame(self):
        detector = self.module.RTMHandDetector(device="cpu")
        self.assertEqual(self.apis.init_detector.call_args.kwargs["device"], "cpu")
        self.assertTrue(self.apis.init_detector.call_args.args[0].endswith("rtmdet_nano_320-8xb32_hand.py"))
        image = np.array([[[10, 20, 30]]], dtype=np.uint8)
        self.detection(
            [[0, 0, 10, 10], [20, 0, 30, 10], [40, 0, 50, 10], [0, 0, 0, 10], [0, 0, np.nan, 10]],
            scores=[.9, .1, .9, .9, .9], labels=[0, 0, 1, 0, 0],
        )
        boxes, ids = detector.detect(image, 0, 10)
        np.testing.assert_array_equal(boxes, [[0, 0, 10, 10]])
        np.testing.assert_array_equal(ids, [0])
        self.assertIs(self.apis.inference_detector.call_args.args[1], image)
        np.testing.assert_array_equal(image, [[[10, 20, 30]]])
        self.detection([])
        boxes, ids = detector.detect(image, 1, 10)
        self.assertEqual(boxes.shape, (0, 4))
        self.assertEqual(ids.shape, (0,))
        self.detection([[1, 0, 11, 10]])
        _, ids = detector.detect(image, 2, 10)
        np.testing.assert_array_equal(ids, [0])

    def test_hand_pose_model_and_color_order(self):
        estimator = self.estimator_module.RTMPoseEstimator("RTMPose-m Hand5", device="cpu")
        self.assertEqual(estimator.number_of_keypoints, 21)
        config, checkpoint = self.apis.init_model.call_args.args
        self.assertTrue(config.endswith("rtmpose-m_8xb256-210e_hand5-256x256.py"))
        self.assertIn("hand5", checkpoint)
        image = np.array([[[10, 20, 30]]], dtype=np.uint8)
        boxes = np.array([[0, 0, 10, 10]])
        estimator.estimate(image, boxes)
        self.assertIs(self.apis.inference_topdown.call_args.args[1], image)
        np.testing.assert_array_equal(image, [[[10, 20, 30]]])
        self.apis.inference_topdown.reset_mock()
        self.assertEqual(estimator.estimate(image, []), [])
        self.apis.inference_topdown.assert_not_called()
        with self.assertRaises(ValueError):
            self.estimator_module.RTMPoseEstimator("hand", device="cpu")

    def test_hand_video_produces_21_rows_with_roi_and_hand_id(self):
        # Exercise the real processor and hand wrappers with inference APIs replaced.
        fixture = pipeline_tests.PosePipelineTests()
        fixture.setUp()
        points = SimpleNamespace(
            keypoints=np.ones((1, 21, 2), dtype=float),
            keypoints_visible=np.ones((1, 21)),
            keypoint_scores=np.full((1, 21), .9),
        )
        pose = MagicMock()
        pose.pred_instances.cpu.return_value.numpy.return_value = points
        self.apis.inference_topdown.return_value = [pose]
        self.detection([[0, 0, 10, 10]])
        detector = self.module.RTMPoseHandDetector(show=False, device="cpu")
        detector.set_cap(fixture.cap)
        with patch.object(self.processor_module.cv2, "destroyAllWindows"):
            detector.detect(roi=True)
        result = detector.get_result()
        self.assertEqual(result.index.tolist(), [(0, "0", i) for i in range(21)])
        np.testing.assert_array_equal(result["x"], np.full(21, 101.))
        np.testing.assert_array_equal(result["y"], np.full(21, 201.))
        self.assertEqual(result.columns.tolist(), ["x", "y", "visible", "score", "timestamp"])


if __name__ == "__main__":
    unittest.main()
