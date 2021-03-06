import numpy as np
import pathlib
import xml.etree.ElementTree as ET
import cv2


class VOCDataset:

    def __init__(self, root, transform=None, target_transform=None, is_test=False, keep_difficult=False):
        """Dataset for VOC data.
        Args:
            root: the root of the VOC2007 or VOC2012 dataset, the directory contains the following sub-directories:
                Annotations, ImageSets, JPEGImages, SegmentationClass, SegmentationObject.
        """
        self.root = pathlib.Path(root)
        # self.root = root
        self.transform = transform
        self.target_transform = target_transform
        if is_test:
            image_sets_file = self.root / "test.txt"
            # image_sets_file = self.root / "trainval.txt"
        else:
            image_sets_file = self.root / "trainval.txt"
        self.ids = VOCDataset._read_image_ids(image_sets_file)
        self.keep_difficult = keep_difficult

        self.class_names = ('BACKGROUND',
            'qqq'
        )
        self.class_dict = {class_name: i for i, class_name in enumerate(self.class_names)}

    def __getitem__(self, index):
        image_id = self.ids[index]
        boxes, labels, is_difficult = self._get_annotation(image_id)
        if not self.keep_difficult:
            boxes = boxes[is_difficult == 0]
            labels = labels[is_difficult == 0]
        # print(image_id)
        # print('===', boxes.shape)
        image = self._read_image(image_id)
        mask = self._read_mask(image_id)


        if self.transform:
            image, boxes, labels, mask = self.transform(image, boxes, labels, mask)
        if self.target_transform:
            boxes, labels = self.target_transform(boxes, labels)

        # image = image.cpu().numpy().astype(np.float32).transpose((1, 2, 0))
        # mask = mask.cpu().numpy().astype(np.float32)
        # cv2.imshow("image",image)
        # cv2.imshow("mask", mask)
        # cv2.waitKey(0)

        return image, boxes, labels, mask

    def get_image(self, index):
        image_id = self.ids[index]
        image = self._read_image(image_id)
        mask = self._read_mask(image_id)
        if self.transform:
            image, mask, _ = self.transform(image, mask)
        return image, mask

    def get_pred_image(self, index):
        image_id = self.ids[index]
        image = self._read_image(image_id)
        if self.transform:
            image = self.transform(image)
        return image

    def get_ori_image(self, index):
        image_id = self.ids[index]
        image = self._read_image(image_id)
        return image

    def get_annotation(self, index):
        image_id = self.ids[index]
        return image_id, self._get_annotation(image_id)

    def __len__(self):
        return len(self.ids)

    @staticmethod
    def _read_image_ids(image_sets_file):
        ids = []
        with open(image_sets_file) as f:
            for line in f:
                ids.append(line.rstrip())
        return ids

    def _get_annotation(self, image_id):
        annotation_file = self.root / f"Annotations/{image_id}.xml"
        objects = ET.parse(annotation_file).findall("object")
        boxes = []
        labels = []
        is_difficult = []
        for object in objects:
            class_name = object.find('name').text.lower().strip()
            # polygon = object.find('polygon')
            # # VOC dataset format follows Matlab, in which indexes start from 0
            #
            # point0 = polygon.find('point0').text.split(',')
            # point1 = polygon.find('point1').text.split(',')
            # point2 = polygon.find('point2').text.split(',')
            # point3 = polygon.find('point3').text.split(',')
            # xmin = min([int(point0[0]),int(point1[0]),int(point2[0]),int(point3[0])]) - 1
            # ymin = min([int(point0[1]),int(point1[1]),int(point2[1]),int(point3[1])]) - 1
            # xmax =max([int(point0[0]),int(point1[0]),int(point2[0]),int(point3[0])]) - 1
            # ymax =max([int(point0[1]),int(point1[1]),int(point2[1]),int(point3[1])]) - 1
            # boxes.append([float(xmin), float(ymin), float(xmax), float(ymax)])
            bbox = object.find('bndbox')
            # VOC dataset format follows Matlab, in which indexes start from 0
            x1 = float(bbox.find('xmin').text)
            y1 = float(bbox.find('ymin').text)
            x2 = float(bbox.find('xmax').text)
            y2 = float(bbox.find('ymax').text)
            boxes.append([x1, y1, x2, y2])
            labels.append(self.class_dict[class_name])
            is_difficult_str = object.find('difficult').text
            is_difficult.append(int(is_difficult_str) if is_difficult_str else 0)

        return (np.array(boxes, dtype=np.float32),
                np.array(labels, dtype=np.int64),
                np.array(is_difficult, dtype=np.uint8))

    def _read_image(self, image_id):
        image_file = self.root / f"Images/{image_id}.png"

        image = cv2.imread(str(image_file))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        max_edge = max(image.shape[0],image.shape[1])
        # image = cv2.copyMakeBorder(image, 0, max_edge - image.shape[0], 0, max_edge - image.shape[1],cv2.BORDER_CONSTANT)

        return image

    def _read_mask(self, image_id):
        mask_file = self.root / f"Segmentations/{image_id}.png"
        # print(image_file)
        mask = cv2.imread(str(mask_file))
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        max_edge = max(mask.shape[0],mask.shape[1])
        # mask = cv2.copyMakeBorder(mask, 0, max_edge - mask.shape[0], 0, max_edge - mask.shape[1],cv2.BORDER_CONSTANT)

        return mask


