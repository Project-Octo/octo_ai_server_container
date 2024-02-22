import os

from flask import Flask, request, jsonify
from google.cloud import storage
from google.cloud import firestore

from ultralytics import YOLO
import os

import cv2

from PIL import Image
import json

import uuid

app = Flask(__name__)


def authenticate_implicit_with_adc(project_id="your-google-cloud-project-id"):
    """
    When interacting with Google Cloud Client libraries, the library can auto-detect the
    credentials to use.

    // TODO(Developer):
    //  1. Before running this sample,
    //  set up ADC as described in https://cloud.google.com/docs/authentication/external/set-up-adc
    //  2. Replace the project variable.
    //  3. Make sure that the user account or service account that you are using
    //  has the required permissions. For this sample, you must have "storage.buckets.list".
    Args:
        project_id: The project id of your Google Cloud project.
    """

    # This snippet demonstrates how to list buckets.
    # *NOTE*: Replace the client created below with the client required for your application.
    # Note that the credentials are not specified when constructing the client.
    # Hence, the client library will look for credentials using ADC.
    storage_client = storage.Client(project=project_id)

def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The ID of your GCS object
    # source_blob_name = "storage-object-name"

    # The path to which the file should be downloaded
    # destination_file_name = "local/path/to/file"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    print(
        "Downloaded storage object {} from bucket {} to local file {}.".format(
            source_blob_name, bucket_name, destination_file_name
        )
    )



@app.route("/run-video-ai", methods=["POST"])
def video_analysis():
    data = request.json
    video_name = data["video_name"]
    folder_uuid = str(uuid.uuid4())

    # Authenticate with Google Cloud Storage
    authenticate_implicit_with_adc()

    download_blob("diver-logbook-videos", video_name + ".mp4", video_name + ".mp4")

    arr = video_name.split('_')
    user_id = arr[0]
    date = arr[1]
    lat = arr[2]
    lon = (arr[3]).replace('.mp4', '')

    # get images folder path
    img_folder_path = os.path.join(os.getcwd(), "images")
    print(img_folder_path)
    video_folder_path = os.path.join(os.getcwd(), "videos")
    print(video_folder_path)
    results_images_folder_path = os.path.join(os.getcwd() ,folder_uuid)
    print(results_images_folder_path)

    # Create a folder to save the images
    if not os.path.exists(img_folder_path):
        os.makedirs(img_folder_path)
    if not os.path.exists(video_folder_path):
        os.makedirs(video_folder_path)
    if not os.path.exists(results_images_folder_path):
        os.makedirs(results_images_folder_path)

    cap = cv2.VideoCapture(video_name + ".mp4")

    if not cap.isOpened():
        raise Exception("Could not open the video file.")

    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    interval = 5 # 인터벌 조정 가능. 실제 다이빙 영상에서는 10초 이상 권장

    frame_count = 0
    success, image = cap.read()
    while success:
        if frame_count % (frame_rate * interval) < 1:
            cv2.imwrite(os.path.join(img_folder_path, f'{video_name}_{frame_count}.jpg'), image)
        success, image = cap.read()
        frame_count += 1

    cap.release()

    model = YOLO('model.pt')
    image_list = os.listdir(img_folder_path)
    image_list = [os.path.join(img_folder_path, img) for img in image_list]
    results = model(image_list)

    # 결과 처리
    json_data = []

    for i, r in enumerate(results):
        img_path = image_list[i]
        image = Image.open(img_path)
        detections = json.loads(r.tojson())
        for detection in detections:
            if detection:

                # 바운딩 박스 추출 및 저장
                box = detection['box']
                cropped_image = image.crop((box['x1'], box['y1'], box['x2'], box['y2']))
                detected_id = uuid.uuid4()
                save_path = f"{folder_uuid}/{detected_id}.png"
                cropped_image.save(save_path)

                # JSON 데이터 생성
                json_data.append({
                    'user_id': user_id,
                    'date': date,
                    'lat': lat,
                    'lon': lon,
                    'species': detection['name'],
                    'img_path': save_path,
                    'detected_id': str(detected_id),
                })

    # upload folder_uuid folder to GCS bucket "detected-fishes"
    storage_client = storage.Client()
    bucket = storage_client.bucket("detected-fishes")
    for file in os.listdir(folder_uuid):
        blob = bucket.blob(f"{folder_uuid}/{file}")
        blob.upload_from_filename(os.path.join(folder_uuid, file))

    # upload json to firestore
    db = firestore.Client()
    doc_ref = db.collection("DetectedFishes").document(folder_uuid)
    doc_ref.set({
        'results': json_data,
    })

    # JSON 파일 저장
    return jsonify({"message": "Video analysis is complete."})



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))