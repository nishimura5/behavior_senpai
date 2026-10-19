import importlib.util
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def load_module(name, dependencies):
    """Load the pipeline with fake inference APIs; no GPU or weights required."""
    path = Path(__file__).resolve().parents[1] / "src" / "behavior_senpai" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, dependencies):
        spec.loader.exec_module(module)
    return module


def tensor(value):
    result = MagicMock()
    result.cpu.return_value.numpy.return_value = np.array(value)
    return result


class PosePipelineTests(unittest.TestCase):
    def setUp(self):
        self.registry = MagicMock()
        self.structures = MagicMock()
        self.processor_module = load_module("pose_video_processor", {
            "mmpose.registry": self.registry,
            "mmpose.structures": self.structures,
        })
        self.detector = MagicMock()
        self.detector.detect.return_value = (np.array([[0, 0, 20, 20]]), np.array([7]))
        self.estimator = MagicMock(number_of_keypoints=2)
        prediction = SimpleNamespace(
            keypoints=np.array([[[10., 20.], [30., 40.]]]),
            keypoints_visible=np.array([[1., 0.]]),
            keypoint_scores=np.array([[0.9, 0.2]]),
        )
        instance = MagicMock()
        instance.cpu.return_value.numpy.return_value = prediction
        self.estimator.estimate.return_value = [SimpleNamespace(pred_instances=instance)]
        self.cap = MagicMock(left_top_point=(100, 200))
        self.cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_COUNT: 1,
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480,
            cv2.CAP_PROP_POS_MSEC: 125.,
        }[prop]
        frame = np.zeros((2, 2, 3), dtype=np.uint8)
        frame[:] = [10, 20, 30]
        self.cap.read.return_value = (True, frame)
        self.cap.get_roi_frame.return_value = (True, frame)

    def processor(self, show=False):
        processor = self.processor_module.PoseVideoProcessor(self.detector, self.estimator, show=show)
        processor.set_cap(self.cap)
        return processor

    def test_video_output_preserves_schema_ids_scores_and_threshold(self):
        processor = self.processor()
        with patch.object(self.processor_module.cv2, "destroyAllWindows"):
            processor.detect()
        result = processor.get_result()
        self.assertEqual(result.index.names, ["frame", "member", "keypoint"])
        self.assertEqual(result.index.tolist(), [(0, "7", 0), (0, "7", 1)])
        self.assertEqual(result.columns.tolist(), ["x", "y", "visible", "score", "timestamp"])
        self.assertIsInstance(result, pd.DataFrame)
        np.testing.assert_allclose(result.to_numpy(), [[10, 20, 1, .9, 125], [0, 0, 0, .2, 125]])
        image = self.detector.detect.call_args.args[0]
        np.testing.assert_array_equal(image[0, 0], [10, 20, 30])
        self.assertIs(image, self.cap.read.return_value[1])
        self.assertIs(self.estimator.estimate.call_args.args[0], image)
        self.assertEqual(self.detector.detect.call_args.kwargs, {"frame_id": 0, "video_len": 1})

    def test_roi_offsets_match_existing_behavior_including_masked_points(self):
        processor = self.processor()
        with patch.object(self.processor_module.cv2, "destroyAllWindows"):
            processor.detect(roi=True)
        np.testing.assert_array_equal(processor.get_result()[["x", "y"]], [[110, 220], [100, 200]])
        self.cap.get_roi_frame.assert_called_once()
        self.cap.read.assert_not_called()

    def test_empty_detections_skip_pose_and_return_empty_dataframe(self):
        self.detector.detect.return_value = (np.empty((0, 4)), np.array([]))
        processor = self.processor()
        with patch.object(self.processor_module.cv2, "destroyAllWindows"):
            processor.detect()
        self.estimator.estimate.assert_not_called()
        self.assertTrue(processor.get_result().empty)
        self.assertEqual(processor.get_result().index.names, ["frame", "member", "keypoint"])

    def test_drawing_and_exit_preserve_current_frame_exclusion(self):
        processor = self.processor(show=True)
        frame = self.cap.read.return_value[1]
        self.registry.VISUALIZERS.build.return_value.get_image.return_value = frame
        with patch.object(self.processor_module.cv2, "imshow"), \
                patch.object(self.processor_module.cv2, "waitKey", return_value=ord("x")), \
                patch.object(self.processor_module.cv2, "destroyAllWindows"), \
                patch.object(self.processor_module.vcap, "resize_frame", return_value=(1, frame)), \
                patch.object(self.processor_module.img_draw, "put_frame_pos"), \
                patch.object(self.processor_module.img_draw, "put_message"):
            processor.detect()
        self.registry.VISUALIZERS.build.return_value.add_datasample.assert_called_once()
        self.assertTrue(processor.get_result().empty)

    def test_empty_detections_still_show_video_and_allow_exit(self):
        self.detector.detect.return_value = (np.empty((0, 4)), np.array([]))
        self.cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_COUNT: 3,
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480,
            cv2.CAP_PROP_POS_MSEC: 125.,
        }[prop]
        processor = self.processor(show=True)
        frame = self.cap.read.return_value[1]
        with patch.object(self.processor_module.cv2, "imshow") as imshow, \
                patch.object(self.processor_module.cv2, "waitKey", return_value=ord("x")) as wait_key, \
                patch.object(self.processor_module.cv2, "destroyAllWindows"), \
                patch.object(self.processor_module.vcap, "resize_frame", return_value=(1, frame)), \
                patch.object(self.processor_module.img_draw, "put_frame_pos"), \
                patch.object(self.processor_module.img_draw, "put_message") as put_message:
            processor.detect()
        imshow.assert_called_once_with("dst", frame)
        wait_key.assert_called_once_with(1)
        self.cap.read.assert_called_once()
        self.estimator.estimate.assert_not_called()
        self.structures.merge_data_samples.assert_not_called()
        self.registry.VISUALIZERS.build.return_value.add_datasample.assert_not_called()
        self.assertTrue(processor.get_result().empty)
        self.assertTrue(any(call.args[1] == "No detections" for call in put_message.call_args_list))

    def test_qdtrack_filters_boxes_and_ids_together(self):
        apis = MagicMock()
        module = load_module("rtmpose_detector", {
            "mmdet.apis": apis,
            "mmdet.utils": MagicMock(),
            "mmengine.registry": MagicMock(),
            "behavior_senpai.pose_video_processor": self.processor_module,
            "behavior_senpai.rtmpose_estimator": MagicMock(),
        })
        tracker = module.QDTrackDetector()
        instances = SimpleNamespace(
            bboxes=tensor([[1, 2, 3, 4], [5, 6, 7, 8]]),
            labels=tensor([1, 0]), instances_id=tensor([11, 22]),
        )
        sample = SimpleNamespace(video_data_samples=[SimpleNamespace(pred_track_instances=instances)])
        for inference_result in [sample, [sample]]:
            apis.inference_mot.return_value = inference_result
            boxes, ids = tracker.detect("image", frame_id=3, video_len=10)
            np.testing.assert_array_equal(boxes, [[5, 6, 7, 8]])
            np.testing.assert_array_equal(ids, [22])
        apis.inference_mot.assert_called_with(tracker.track_model, "image", frame_id=3, video_len=10)

        # The existing entry point composes the new classes and retains the video API.
        with patch.object(module, "QDTrackDetector", return_value=self.detector), \
                patch.object(module, "RTMPoseEstimator", return_value=self.estimator) as estimator_class:
            detector = module.RTMPoseDetector("RTMPose-x Halpe26", show=False)
        estimator_class.assert_called_once_with("RTMPose-x Halpe26")
        detector.set_cap(self.cap)
        with patch.object(self.processor_module.cv2, "destroyAllWindows"):
            detector.detect(roi=False)
        self.assertEqual(detector.get_result().index.tolist(), [(0, "7", 0), (0, "7", 1)])

    def test_pose_models_and_empty_boxes(self):
        apis = MagicMock()
        module = load_module("rtmpose_estimator", {"mmpose.apis": apis})
        for model, count in [("RTMPose-x Halpe26", 26), ("RTMPose-x WholeBody133", 133), ("RTMW-x WholeBody133", 133)]:
            with self.subTest(model=model):
                estimator = module.RTMPoseEstimator(model)
                self.assertEqual(estimator.number_of_keypoints, count)
                self.assertEqual(estimator.estimate("image", []), [])
                apis.inference_topdown.assert_not_called()
                boxes = np.array([[1, 2, 3, 4]])
                image = np.array([[[10, 20, 30]]], dtype=np.uint8)
                self.assertIs(estimator.estimate(image, boxes), apis.inference_topdown.return_value)
                apis.inference_topdown.assert_called_once_with(estimator.model, image, boxes)
                self.assertIs(apis.inference_topdown.call_args.args[1], image)
                apis.inference_topdown.reset_mock()
        with self.assertRaises(ValueError):
            module.RTMPoseEstimator("unknown")


if __name__ == "__main__":
    unittest.main()
