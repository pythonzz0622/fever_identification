import fiftyone.brain as fob
import json
import fiftyone as fo
from pycocotools.coco import COCO
import os
import re

# get groundtruth info
coco = COCO('../dataset/coco.json')


def min_max(bbox, img_w, img_h):
    x, w = [x / img_w for x in bbox[::2]]
    y, h = [x / img_h for x in bbox[1::2]]
    return [x, y, w, h]


def mask_slice(bbox, mask):
    x1, y1, w, h = bbox
    return mask[y1:y1+h, x1:x1+w]


img_path_to_id = {re.sub('.jpg', '', os.path.basename(
    x['file_name'])): x['id'] for x in coco.loadImgs(coco.getImgIds())}

img_path_list = ['../dataset/' + anno['file_name']
                 for anno in coco.loadImgs(coco.getImgIds())]

# Create a dataset from a glob pattern of images
dataset = fo.Dataset.from_images(img_path_list)

# id : category 매칭
id_to_cat = {v['id']: v['name'] for v in coco.loadCats(coco.getCatIds())}

# img 별 iteration
samples = []
for img_id in coco.getImgIds():
    # fiftyone sample에 img 삽입
    sample = fo.Sample(filepath='../dataset/' +
                       coco.loadImgs(img_id)[0]['file_name'])
    detections = []
    img_info = coco.loadImgs(ids=img_id)[0]
    # annotation 별 iteration
    for ann_id in coco.getAnnIds(imgIds=img_id):
        obj = coco.loadAnns(ann_id)[0]
        label = id_to_cat[obj['category_id']]
        bbox = min_max(obj['bbox'], img_info['width'], img_info['height'])

        # fiftyone detections sample에 annotation 삽입
        detections.append(
            fo.Detection(label=label,
                         bounding_box=bbox,
                         mask=mask_slice(bbox=obj['bbox'],
                                         mask=coco.annToMask(obj)))
        )

    if detections:
        sample['ground_truth'] = fo.Detections(detections=detections)

    samples.append(sample)

# dataset title 넣기
dataset = fo.Dataset()
dataset.add_samples(samples)

if __name__ == "__main__":
    session = fo.launch_app(dataset, port=8842, address="0.0.0.0")
    session.wait()
