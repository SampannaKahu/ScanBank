import os
import uuid
import shutil
import zipfile
import glob
import logging
import torch
import json
import typing
import argparse
from PIL import Image
from multiprocessing import Pool
from functools import partial
from gold_standard.convert_VIA_to_coco import build_image, build_annotation

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename=os.path.basename(__file__).split('.')[0] + '.log')
logger = logging.getLogger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)


def unzip_zip_file(zip_file_path: str, extract_dir: str = '/tmp') -> typing.Tuple[
    typing.List[str], typing.List[str]]:
    """
    Takes in a zip file path. Unzips it in a temporary directory. And returns the list of the files unzipped.
    Works only for flat file-structured zips.
    :param zip_file_path: path os the zip file.
    :param extract_dir: The directory to extract the data into.
    :return: the list of path of the contents of the zip (all, png and pt)
    """
    process_unzip_dir = os.path.join(extract_dir, str(os.getpid()) + '_' + str(uuid.uuid1()).replace('-', '_'))
    os.makedirs(process_unzip_dir, exist_ok=True)
    zip = zipfile.ZipFile(zip_file_path)
    zip.extractall(path=process_unzip_dir)
    zip.close()
    file_list = os.listdir(os.path.join(process_unzip_dir, 'tmp'))
    png_paths = [os.path.join(process_unzip_dir, 'tmp', path) for path in file_list if '.png' in path]
    pt_paths = [os.path.join(process_unzip_dir, 'tmp', path) for path in file_list if '.pt' in path]
    assert len(png_paths) == len(pt_paths)
    png_paths = sorted(png_paths)
    pt_paths = sorted(pt_paths)
    return png_paths, pt_paths


def _setup_directories(_dataset_dir: str, _image_save_dir: str, _tmp_extract_dir: str):
    os.makedirs(_dataset_dir, exist_ok=True)
    os.makedirs(_image_save_dir, exist_ok=True)
    shutil.rmtree(_tmp_extract_dir, ignore_errors=True)
    os.makedirs(_tmp_extract_dir, exist_ok=True)


def convert_pregenerated_annotations_to_coco(_annotation_save_path: str,
                                             _job_output_directory: str,
                                             _tmp_extract_dir: str,
                                             _image_save_dir: str,
                                             _batch_size: int = 100,
                                             _pool_size: int = 8,
                                             _coco_dataset_template_path: str = '/home/sampanna/workspace/bdts2/deepfigures-open/hpc/post_process/coco_dataset_template.json'):
    if os.path.exists(_annotation_save_path):
        dataset = json.load(open(_annotation_save_path))
    else:
        dataset = json.load(open(_coco_dataset_template_path))

    current_image_id = max([image['id'] for image in dataset['images']], default=0) + 1
    current_annotation_id = max([annotation['id'] for annotation in dataset['annotations']], default=0) + 1

    zip_paths = glob.glob(os.path.join(_job_output_directory, '**.zip'), recursive=True)
    batches = [zip_paths[i:i + _batch_size] for i in range(0, len(zip_paths), _batch_size)]
    for batch in batches:
        with Pool(processes=_pool_size) as pool:
            result_list = pool.map(
                partial(unzip_zip_file, extract_dir=_tmp_extract_dir),
                batch
            )
        png_paths = []
        pt_paths = []
        for result_tuple in result_list:
            png_paths = png_paths + result_tuple[0]
            pt_paths = pt_paths + result_tuple[1]

        for idx, png_path in enumerate(png_paths):
            pt_path = pt_paths[idx]
            logger.info("Idx: {}, Png path: {}, pt path: {}.".format(idx, png_path, pt_path))
            if png_path.split('.png')[0] != pt_path.split('.pt')[0]:
                logger.warning("Found an instance when the pt path is not the same as png path. Skipping")
                logger.warning("pt path: {}. Png path: {}".format(pt_path, png_path))
                continue

            _image_save_path = os.path.join(_image_save_dir, str(current_image_id) + '.png')
            os.rename(png_path, _image_save_path)
            img = Image.open(_image_save_path)
            dataset['images'].append(
                build_image(image_path=_image_save_path, image_id=current_image_id, height=img.size[0],
                            width=img.size[1])
            )

            tensor = torch.load(pt_path)
            for bb in tensor:
                dataset['annotations'].append(
                    build_annotation(x1=bb[1].item(), y1=bb[3].item(), height=bb[4].item() - bb[3].item(),
                                     width=bb[2].item() - bb[1].item(),
                                     annotation_id=current_annotation_id,
                                     image_id=current_image_id,
                                     category_id=1)
                )
                current_annotation_id = current_annotation_id + 1
            current_image_id = current_image_id + 1

        # Cleanup the temp directory.
        shutil.rmtree(_tmp_extract_dir, ignore_errors=True)
        os.makedirs(_tmp_extract_dir, exist_ok=True)

        # checkpoint the annotation file.
        json.dump(dataset, open(_annotation_save_path, mode='w'), indent=2)
        logger.info("Successfully saved annotations after processing zipfile batch paths: {}".format(batch))
        logger.info("Current image id: {}, current annotation id: {}".format(current_image_id, current_annotation_id))


if __name__ == "__main__":
    dataset_dir = '/home/sampanna/workspace/bdts2/deepfigures-results/arxiv_coco_dataset'

    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_dir', default=dataset_dir, type=str)
    parser.add_argument('--annotation_save_path', default=os.path.join(dataset_dir, 'annotations.json'), type=str)
    parser.add_argument('--image_save_dir', type=int, default=os.path.join(dataset_dir, 'images'))
    parser.add_argument('--tmp_extract_dir', type=int, default=os.path.join(dataset_dir, 'tmp'))
    parser.add_argument('--batch_size', type=int, default=100)
    parser.add_argument('--pool_size', type=int, default=8)
    parser.add_argument('--job_output_directory',
                        default='/home/sampanna/workspace/bdts2/deepfigures-results/pregenerated_training_data/377269',
                        type=str)
    parser.add_argument('--coco_dataset_template_path',
                        default='/home/sampanna/workspace/bdts2/deepfigures-open/hpc/post_process/coco_dataset_template.json',
                        type=str)
    args = parser.parse_args()

    # Clean-up and make any directories necessary to run the job.
    _setup_directories(_dataset_dir=args.dataset_dir,
                       _image_save_dir=args.image_save_dir,
                       _tmp_extract_dir=args.tmp_extract_dir)

    # Start the conversion.
    convert_pregenerated_annotations_to_coco(_annotation_save_path=args.annotation_save_path,
                                             _job_output_directory=args.job_output_directory,
                                             _tmp_extract_dir=args.tmp_extract_dir,
                                             _image_save_dir=args.image_save_dir,
                                             _batch_size=args.batch_size,
                                             _pool_size=args.pool_size,
                                             _coco_dataset_template_path=args.coco_dataset_template_path)
