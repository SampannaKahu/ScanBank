import os
import csv
import json
import logging
import argparse

from PIL import Image

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)


def build_annotation(x1: int, y1: int, height: int, width: int, annotation_id: int, image_id: int, category_id: int):
    """
    Sample annotation:
    {
        "segmentation": [
          [510.66,423.01,511.72,420.03,510.45,416,510.45,423.01]
        ],
        "area": 702.1057499999998,
        "iscrowd": 0,
        "image_id": 289343,
        "bbox": [
          473.07,
          395.93,
          38.65,
          28.67
        ],
        "category_id": 18,
        "id": 1768
    }
    """
    # x1, y1, x2, y2 = bb[1].item(), bb[3].item(), bb[2].item(), bb[4].item()
    x2 = x1 + width
    y2 = y1 + height
    return {
        "id": annotation_id,
        "image_id": image_id,
        "category_id": category_id,
        "segmentation": [[x1, y1, x2, y1, x2, y2, x1, y2]],
        "area": width * height,
        "bbox": [x1, y1, width, height],
        "iscrowd": 0
    }


def build_image(image_path: str, image_id: int, height: int, width: int):
    """
    Sample image:
    {
        "license": 4,
        "file_name": "000000397133.jpg",
        "coco_url": "http://images.cocodataset.org/val2017/000000397133.jpg",
        "height": 427,
        "width": 640,
        "date_captured": "2013-11-14 17:02:52",
        "flickr_url": "http://farm7.staticflickr.com/6116/6255196340_da26cf2c9e_z.jpg",
        "id": 397133
    }
    """
    return {
        "license": 2,  # TODO: Confirm this.
        "file_name": os.path.basename(image_path),
        "coco_url": "",
        "height": height,
        "width": width,
        "date_captured": "2020-05-20 01:00:00",
        "flickr_url": "",
        "id": image_id
    }


def get_image_name_to_row_list_dict(_annotations_csv_file: str) -> dict:
    image_name_to_row_list_dict = {}
    with open(_annotations_csv_file) as fp:
        reader = csv.reader(fp)
        header_done = False
        for row in reader:
            if not header_done:
                header_done = True
                continue
            image_name = row[0]
            row_list = image_name_to_row_list_dict.get(image_name, [])
            rect_dict = json.loads(row[5])
            if rect_dict:
                row_list.append(rect_dict)
            image_name_to_row_list_dict[image_name] = row_list
    return image_name_to_row_list_dict


def create_annotations_for_image_names(image_names: list, _image_name_to_row_list_dict: dict, _images_dir: str,
                                       _output_json_path: str,
                                       _coco_dataset_template_path: str = '/home/sampanna/workspace/bdts2/deepfigures-open/hpc/post_process/coco_dataset_template.json'):
    dataset = json.load(open(_coco_dataset_template_path))
    image_id = 1
    annotation_id = 1
    for image_name in image_names:
        image_path = os.path.join(_images_dir, image_name)
        img = Image.open(image_path)
        image_json = build_image(image_path=image_name, image_id=image_id, height=img.size[1], width=img.size[0])
        dataset['images'].append(image_json)
        row_list = _image_name_to_row_list_dict[image_name]
        for row in row_list:
            annotation_json = build_annotation(x1=row['x'], y1=row['y'], width=row['width'], height=row['height'],
                                               annotation_id=annotation_id, image_id=image_id, category_id=1)
            dataset['annotations'].append(annotation_json)
            annotation_id = annotation_id + 1
        image_id = image_id + 1

    json.dump(dataset, open(_output_json_path, mode='w'), indent=2)
    return dataset


if __name__ == "__main__":
    dataset_dir = '/home/sampanna/gold_standard_generation/final_gold_standard_dataset'
    annotations_csv_file = '/home/sampanna/gold_standard_generation/final_gold_standard_dataset/annotations.csv'

    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_dir', default=dataset_dir, type=str)
    parser.add_argument('--annotations_csv_file', default=annotations_csv_file, type=str)
    parser.add_argument('--images_dir', default=os.path.join(dataset_dir, 'images'), type=str)
    parser.add_argument('--coco_dataset_template_path',
                        default='/home/sampanna/workspace/bdts2/deepfigures-open/hpc/post_process/coco_dataset_template.json',
                        type=str)
    args = parser.parse_args()

    image_name_to_row_list_dict = get_image_name_to_row_list_dict(_annotations_csv_file=args.annotations_csv_file)
    image_names = list(image_name_to_row_list_dict.keys())
    create_annotations_for_image_names(image_names=image_names,
                                       _image_name_to_row_list_dict=image_name_to_row_list_dict,
                                       _images_dir=args.images_dir,
                                       _output_json_path=os.path.join(args.dataset_dir, 'annotations.json'),
                                       _coco_dataset_template_path=args.coco_dataset_template_path)
