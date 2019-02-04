# Connoisseur #

Connoisseur is a machine learning service for BisQue which manages ML models and their creation/execution. Currently it only supports a deep learning framework Caffe.

### Issues to solve ###

* long running requests must run as celery tasks
* locking models is needed to protect binaries from parallel operations
* transaction during request is bad, need to update status of the resource in the middle of a long running request
* physical location for models
* store for templates
* need to capture output from long running caffe binary
* hierarchical models
* models loaded separately in each process/thread and thus will use more RAM and will be slower

INFO API
==============

* GET /connoisseur
or
* GET /connoisseur/info

CLASSIFICATION API
====================

* GET /connoisseur/MODEL_ID/classify:IMAGE_ID
* GET /connoisseur/MODEL_ID/classify:IMAGE_ID[/method:points] # default, classify uniformly distributed points
* GET /connoisseur/MODEL_ID/classify:IMAGE_ID[/method:points_random] # classify randomly distributed points
* GET /connoisseur/MODEL_ID/classify:IMAGE_ID[/method:segmentation] # segment image pixels producing image mask with class labels
* GET /connoisseur/MODEL_ID/classify:IMAGE_ID[/method:regions] # partition image into regions producing low-res polygons
* 
* GET /connoisseur/MODEL_ID/classify:IMAGE_ID[/method:salient] #
* GET /connoisseur/MODEL_ID/classify:IMAGE_ID[/method:salient_uniform] #
* GET /connoisseur/MODEL_ID/classify:IMAGE_ID[/method:image] #

Parameters for all methods:

* points: number of output points, approximate for some methods
* goodness: % (0-100), minimum goodness for an output point
* border: % (0-100) of the image size, border in pixels will be estimated from image's dimensions


# parameters for point classification random and uniform
* GET /connoisseur/MODEL_ID/classify:IMAGE_ID/method:points[/points:10][/goodness:95][/border:5][/format:csv]

format: xml, json, csv, hdf

# parameters for region partitioning
* GET /connoisseur/MODEL_ID/classify:IMAGE_ID/method:regions[/points:10][/goodness:95][/border:5][/format:csv]

format: xml, json, csv, hdf

# parameters for segmentation
* GET /connoisseur/MODEL_ID/classify:IMAGE_ID/method:segmentation[/points:10][/goodness:95][/border:5][/colors:ids]
* GET /connoisseur/MODEL_ID/classify:IMAGE_ID/method:segmentation[/points:10][/goodness:95][/border:5][/colors:colors]

formats: png


MODEL INFO API
================

* GET /connoisseur/MODEL_ID/class:3/sample:1


RESTful API
=============

* GET - request classification, preview or training

Responses:
*     204 Empty results
*     400 Bad Request
*     401 Unauthorized
*     500 Internal Server Error
*     501 Not Implemented

MODEL DEFINITION
==================

See classifier_model.py

CLASSIFIER OUTPUTS
==================

* [table/gobs]
gob type: str | gob label: str | gob vertices: [(x,y,z,...)] | goodness: float | accuracy: float | color: str

* [image/png]
bytes...


STATUS WORKFLOW
==================

1. new
2. classes loaded    <-----   # needs to re-load all files from template and repeat all steps: 3-8
3. classes filtered       |
4. samples loaded    <-----   # needs to re-split the samples and other steps: 5-8
5. samples split          |
6. trained                |
7. validated              |
8. finished          ------

TRAINING WORKFLOW
===================

The model resource is created by the JS UI and initially may only contain a user-given name and a dataset to train on.
After the model resource is created in the system several operations may be requested following a typical training sequence.

1. Define required model parameters
    a. Pick a model template to fine-tune or train from scratch
    b. This should define a "mode", currently point classification but later also fully convolutional

2. Find classes for the model, this will lock the model for current classes and will not allow further changes

3. Create training samples, using parameters defined in the model. This can be repeated to augment the sample list
    a. Absolute minimum number of samples per class
    b. Minimum number of samples to activate sample augmentation

4. Train on available samples
    a. train the model
    b. validate the model and update classes performance

5. Set classes that will be used for classification based on observed performance in the training step

6. Model is ready for recognition

6. Repeat step 3 and further to improve the model


MODEL MODIFICATION API
========================

* GET /connoisseur/create/template:CaffeNet[/dataset:UUID]
* GET /connoisseur/MODEL_ID/update[/classes:init][/classes:filter][/samples:init][/samples:update][/samples:split]
* GET /connoisseur/MODEL_ID/train[/method:finetune][/method:snapshot]
* GET /connoisseur/MODEL_ID/validate