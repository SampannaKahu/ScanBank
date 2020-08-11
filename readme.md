The original readme (readme from the original fork) can be found [here][original-readme].

Master branch docker image build status: [![Build Status](https://travis-ci.org/SampannaKahu/deepfigures-open.svg?branch=master)](https://travis-ci.org/SampannaKahu/deepfigures-open)

## Instructions to run this fork:

#### Create python environment
Use the ``requirements.txt`` from the repository's root to create your python environment.

Another quick way to set up the environment using Anaconda is:

```shell script
ENV_NAME=deepfigures_3 && conda remove --name $ENV_NAME --all -y && conda create --name $ENV_NAME python=3.6 -y && source activate $ENV_NAME && pip install -r /home/sampanna/deepfigures-open/requirements.txt --no-cache-dir
```

#### Install deepfigures package
Activate the above-created python environment, update the PROJECT_SOURCE variable to where you cloned this repository, and run the following commands.
```shell script
# Edit this to point to the location where you cloned this repository.
PROJECT_SOURCE=/home/sampanna/deepfigures-open

# This will remove any previously generated build files. If none are present, it won't do anything.
rm -rf $PROJECT_SOURCE/build \
  $PROJECT_SOURCE/dist \
  $PROJECT_SOURCE/deepfigures_open.egg-info \
  $PROJECT_SOURCE/vendor/tensorboxresnet/.eggs \
  $PROJECT_SOURCE/vendor/tensorboxresnet/build \
  $PROJECT_SOURCE/vendor/tensorboxresnet/dist \
  $PROJECT_SOURCE/vendor/tensorboxresnet/tensorboxresnet.egg-info \
  $PROJECT_SOURCE/vendor/tensorboxresnet/tensorboxresnet/utils/stitch_wrapper.cpp

# Uninstall deepfigures-open and tensorboxresnet, if it is installed in the current environment.
pip uninstall deepfigures-open -y
pip uninstall deepfigures-open -y
pip uninstall tensorboxresnet -y
pip uninstall tensorboxresnet -y

cd $PROJECT_SOURCE

# Install deepfigures-open in the current environment.
python setup.py install

# Install tensorboxresnet in the current environment.
cd vendor/tensorboxresnet && python setup.py install && cd ../..

# Remove any generated build files to keep the source code clean.
rm -rf $PROJECT_SOURCE/build \
  $PROJECT_SOURCE/dist \
  $PROJECT_SOURCE/deepfigures_open.egg-info \
  $PROJECT_SOURCE/vendor/tensorboxresnet/.eggs \
  $PROJECT_SOURCE/vendor/tensorboxresnet/build \
  $PROJECT_SOURCE/vendor/tensorboxresnet/dist \
  $PROJECT_SOURCE/vendor/tensorboxresnet/tensorboxresnet.egg-info \
  $PROJECT_SOURCE/vendor/tensorboxresnet/tensorboxresnet/utils/stitch_wrapper.cpp

```
This will install the deepfigures python package in the current environment which will make our code work.

#### Set AWS credentials. 
If you need you need to download data from AWS, please add your credentials to the ```credentials``` file.
A sample of this file should look like:
```ini
[default]
aws_access_key_id=dummy_sample_credentials
aws_secret_access_key=dummy_sample_credentials_dummy_sample_credentials
aws_session_token=dummy_sample_credentials_dummy_sample_credentials_dummy_sample_credentials_dummy_sample_credentials_dummy_sample_credentials_dummy_sample_credentials_dummy_sample_credentials_
```

Also, don't forget to set the ARXIV_DATA_TMP_DIR and ARXIV_DATA_OUTPUT_DIR variables as mentioned in the ```README.md```.

#### Test the pre-built Docker image:
```shell script
sudo docker run --gpus all -it --volume /home/sampanna/deepfigures-results:/work/host-output --volume /home/sampanna/deepfigures-results/31219:/work/host-input sampyash/vt_cs_6604_digital_libraries:deepfigures_gpu_0.0.5 /bin/bash
```
This command will pull the ``sampyash/vt_cs_6604_digital_libraries:deepfigures_gpu_0.0.5`` docker image from Docker Hub, run it and give us bash access to it.
If this image is already pulled, this command will simply run it.
``sampyash/vt_cs_6604_digital_libraries:deepfigures_cpu_0.0.5`` is also available for CPU use-cases.

Note: Please check the latest version before pulling.

In the above command, the first '--volume' argument connects the local output directory with the docker output directory.
The second '--volume' argument does the same for the input directory.
Please modify the local file paths as per your local host system.
More info [here][docker-commandline-run-docs].

Further, the ``--gpus all`` option tells docker to use all the GPUs available on the system.
Try running ``nvidia-smi`` once inside the container to check if GPUs are accessible. 
The ``--gpus all`` option is not required when running the CPU docker image.

#### Generate data:
```shell script
docker run --gpus all -it --volume /home/sampanna/deepfigures-results:/work/host-output --volume /home/sampanna/deepfigures-results:/work/host-input sampyash/vt_cs_6604_digital_libraries:deepfigures_gpu_0.0.6 python deepfigures/data_generation/arxiv_pipeline.py
```
This command will run the ``deepfigures/data_generation/arxiv_pipeline.py`` script from the source code which will:
- Download data from AWS's requester-pays buckets using the credentials set above.
- Cache this data in the directory ``/work/host-output/download_cache``.
- Unzip and generate the relevant training data.

#### Transform data:
```shell script
docker run --gpus all -it --volume /home/sampanna/deepfigures-results:/work/host-output --volume /home/sampanna/deepfigures-results:/work/host-input sampyash/vt_cs_6604_digital_libraries:deepfigures_cpu_0.0.6 python figure_json_transformer.py
```

```shell script
docker run --gpus all -it --volume /home/sampanna/deepfigures-results:/work/host-output --volume /home/sampanna/deepfigures-results:/work/host-input sampyash/vt_cs_6604_digital_libraries:deepfigures_cpu_0.0.6 python figure_boundaries_train_test_split.py
```

The data generated by the ``arxiv_pipeline.py`` is not in the format needed by ``tensorbox`` for training.
Hence, this command will transform it. The second command will split the data in test and train split.

#### Train the model:
```shell script
python manage.py train /work/host-input/weights/hypes.json /home/sampanna/deepfigures-results /home/sampanna/deepfigures-results
```
Here, the python environment created in one of the steps above should be activated.
- The first argument to ``manage.py`` is the ``train`` command.
- ``/work/host-input/weights/hypes.json`` is the path to the hyper-parameters as visible from inside the docker container.
- ``/home/sampanna/deepfigures-results`` is the host's input directory for the container. This will be linked to ``/work/host-input``.
- ``/home/sampanna/deepfigures-results`` is the host's output directory for the container. This will be linked to ``/work/host-output``.

#### Run detection:
```shell script
python manage.py detectfigures '/home/sampanna/workspace/bdts2/deepfigures-results' '/home/sampanna/workspace/bdts2/deepfigures-results/LD5655.V855_1935.C555.pdf'
```
Here, the python environment created in one of the steps above should be activated.
- The first argument to ``manage.py`` is the ``detectfigures`` command.
- ``'/home/sampanna/workspace/bdts2/deepfigures-results'`` is the host path to the output directory to put the detection results in.
- ``'/home/sampanna/workspace/bdts2/deepfigures-results/LD5655.V855_1935.C555.pdf'`` is the host path to the PDF file to be processes.

## Instructions to run on ARC using [Singularity][singularity-homepage]:
Docker is not available on Virginia Tech's [Advanced Research Computing][vt-arc-homepage] HPC cluster.
However, Singularity can be used to run pre-built Docker images on ARC using singularity.

#### Load the module:
Each time you ssh into either the login node or any of the compute nodes, please lode the Singularity module using:
```shell script
module load singularity/3.3.0
```

#### Create the singularity directory:
```shell script
mkdir /work/cascades/${USER}/singularity
```
Make the directory required for Singularity.

#### Pull the Docker image:
```shell script
singularity pull docker://sampyash/vt_cs_6604_digital_libraries:deepfigures_gpu_0.0.6
```
- This command will pull the given image from Docker Hub.
- This command needs internet access and hence needs to be run on the login node.
- This command will take some time.

#### Run the pulled image:
```shell script
singularity run --nv -B /home/sampanna/deepfigures-results:/work/host-output -B /home/sampanna/deepfigures-results:/work/host-input /work/cascades/sampanna/singularity/vt_cs_6604_digital_libraries_deepfigures_cpu_0.0.6.sif /bin/bash
```
- This command will run the pulled Docker image and give the user the shel access inside the container.
- The ``--nv`` flag is analogous to the  ``--gpus all`` option of Docker.
- The ``-B`` flag is analogous to the ``--volume`` option of Docker.

The executions of the remaining commands is straightforward is left as an exercise to the reader.


## Why was this fork made:
The master branch of the original repository was not working for me. So I debugged and made this fork. Following are the changes which were made.

#### Made changes to the ```Dockerfile```s.

Docker-file was not building (both cpu and gpu). 
There was some error related to 'libjasper1 libjasper-dev not found'. 
Hence, added corresponding changes to the Dockerfile to make them buildable. 
Have also pushed the built images to Docker Hub. Link [here][docker-hub-link]. 
You can simply fetch the two images and re-tag them as ```deepfigures-cpu:0.0.6``` and ```deepfigures-gpu:0.0.6```. 
Further, added the functionality to make read AWS credentials from the ./credentials file. 
    
#### Added the pre-built pdffigures jar.

```pdffigures``` jar has been built and committed in the ```bin``` folder in this repository. Hence, you should not need to build it. Please have java 8 in your system to make it work.

#### scipy version downgrade
 
Version 1.3.0 of scipy does not have imread and imsave in scipy.misc. As a result, the import statement ```from scipy.misc import imread, imsave``` in detections.py was not working. Hence, downgraded the version of scipy to 1.1.0 in requirements.txt. The import worked as a result.

#### sp.optimize was not getting imported.

Imported it separately using ```from scipy import optimize``` and started using it like ```scipy.optimize()```.


[original-readme]: https://github.com/SampannaKahu/deepfigures-open/blob/master/original_readme.md
[docker-hub-link]: https://hub.docker.com/r/sampyash/vt_cs_6604_digital_libraries/tags
[docker-commandline-run-docs]: https://docs.docker.com/engine/reference/commandline/run
[singularity-homepage]: https://singularity.lbl.gov
[vt-arc-homepage]: https://www.arc.vt.edu
