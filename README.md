# Object detection model for detecting fish species in images
#여기 OcTo로고 사진 또는 어플 실행사진 들어가면 좋을 거 같음

## Abstract
This is OcTo's object detection model for processing user videos. It detects various types of fish encountered during diving from user videos. Trained with [YOLOv8](https://github.com/ultralytics/ultralytics), it can detect 53 species of fish, with a performance of Precision 0.727, Recall 0.624, and mAP50 0.665.


## Dataset
We used the Actinopterygii photo data with bounding boxes from the [iNaturalist2017](https://github.com/visipedia/inat_comp/tree/master/2017) dataset. This data consists of 2,571 train boxes and 511 valid boxes, which were further divided into 92%-4%-4% splits for training/validation/testing. The images are taken in various conditions including underwater, out of water, and on the water surface. There is a non-uniform distribution of images per category.

## Evaluation
#여기는 첨부한 물고기 평가 이미지 들어갈 자리
The model detected 235 instances of fish across 182 images. The overall performance of the model is shown with a Precision of 0.727, Recall of 0.624, and mAP50 of 0.665, indicating it is moderately effective in detecting fish in diving videos. However, there are variations in performance across different species.