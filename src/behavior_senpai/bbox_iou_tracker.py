import numpy as np


class BBoxIoUTracker:
    """Assign IDs by greedy, one-to-one IoU matching of xyxy boxes.

    Unmatched tracks retain their last box across max_age missing frames.
    There is no motion or appearance model, so crossings and fast motion
    can switch IDs. IDs describe objects, not handedness or person identity.
    """

    def __init__(self, iou_threshold=0.3, max_age=30):
        if not 0 < iou_threshold <= 1:
            raise ValueError("iou_threshold must be in (0, 1].")
        if not isinstance(max_age, int) or max_age < 0:
            raise ValueError("max_age must be a non-negative integer.")
        self.iou_threshold = iou_threshold
        self.max_age = max_age
        self.reset()

    def reset(self):
        self.tracks = {}
        self.next_id = 0
        self.last_frame_id = None

    def update(self, bboxes, frame_id):
        """Return IDs in bbox order; restarting the frame sequence resets IDs."""
        bboxes = np.asarray(bboxes, dtype=float).reshape(-1, 4)
        if self.last_frame_id is not None and frame_id <= self.last_frame_id:
            self.reset()
        self.last_frame_id = frame_id
        self.tracks = {
            tid: (box, last_seen) for tid, (box, last_seen) in self.tracks.items()
            if frame_id - last_seen <= self.max_age + 1
        }
        track_ids = np.full(len(bboxes), -1, dtype=np.int64)
        if len(bboxes) and self.tracks:
            previous_ids = list(self.tracks)
            previous_boxes = np.array([self.tracks[tid][0] for tid in previous_ids])
            overlaps = self._iou(previous_boxes, bboxes)
            while overlaps.size:
                row, col = np.unravel_index(np.argmax(overlaps), overlaps.shape)
                if overlaps[row, col] < self.iou_threshold:
                    break
                track_ids[col] = previous_ids[row]
                overlaps[row, :] = -1
                overlaps[:, col] = -1

        for idx, box in enumerate(bboxes):
            if track_ids[idx] == -1:
                track_ids[idx] = self.next_id
                self.next_id += 1
            self.tracks[int(track_ids[idx])] = (box.copy(), frame_id)
        return track_ids

    @staticmethod
    def _iou(a, b):
        start = np.maximum(a[:, None, :2], b[None, :, :2])
        end = np.minimum(a[:, None, 2:], b[None, :, 2:])
        intersection = np.prod(np.maximum(end - start, 0), axis=2)
        area_a = np.prod(np.maximum(a[:, 2:] - a[:, :2], 0), axis=1)
        area_b = np.prod(np.maximum(b[:, 2:] - b[:, :2], 0), axis=1)
        union = area_a[:, None] + area_b[None, :] - intersection
        return np.divide(intersection, union, out=np.zeros_like(intersection), where=union > 0)
