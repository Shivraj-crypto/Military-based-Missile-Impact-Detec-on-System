from dataclasses import dataclass
from typing import List

import cv2
import numpy as np


@dataclass
class Detection:
    class_id: int
    confidence: float
    x: int
    y: int
    width: int
    height: int


class YoloExplosionDetector:
    def __init__(
        self,
        cfg_path,
        weights_path,
        class_names,
        conf_threshold=0.5,
        nms_threshold=0.3,
    ):
        self.class_names = class_names
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold

        self.net = cv2.dnn.readNet(str(weights_path), str(cfg_path))
        layer_names = self.net.getLayerNames()
        unconnected = self.net.getUnconnectedOutLayers()
        if isinstance(unconnected, np.ndarray):
            self.output_layers = [layer_names[i - 1] for i in unconnected.flatten()]
        else:
            self.output_layers = [layer_names[unconnected - 1]]

    def detect(self, frame) -> List[Detection]:
        height, width, _ = frame.shape
        blob = cv2.dnn.blobFromImage(
            frame,
            scalefactor=0.00392,
            size=(416, 416),
            mean=(0, 0, 0),
            swapRB=True,
            crop=False,
        )
        self.net.setInput(blob)
        outs = self.net.forward(self.output_layers)

        boxes = []
        confidences = []
        class_ids = []

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = int(np.argmax(scores))
                confidence = float(scores[class_id])
                if confidence < self.conf_threshold:
                    continue

                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(confidence)
                class_ids.append(class_id)

        if not boxes:
            return []

        indexes = cv2.dnn.NMSBoxes(
            boxes,
            confidences,
            score_threshold=self.conf_threshold,
            nms_threshold=self.nms_threshold,
        )

        if len(indexes) == 0:
            return []

        flattened_indexes = indexes.flatten() if isinstance(indexes, np.ndarray) else indexes

        detections: List[Detection] = []
        for i in flattened_indexes:
            x, y, w, h = boxes[i]
            detections.append(
                Detection(
                    class_id=class_ids[i],
                    confidence=confidences[i],
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                )
            )
        return detections
