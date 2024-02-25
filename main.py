import os

from flask import Flask, request, jsonify
from google.cloud import storage
from google.cloud import firestore
import google.auth

from ultralytics import YOLO

import cv2

from PIL import Image
import json

import uuid

app = Flask(__name__)

# Authenticate
credentials, project = google.auth.default()

def download_blob(bucket_name, source_blob_name, destination_file_name):

    storage_client = storage.Client(credentials=credentials, project=project)

    bucket = storage_client.bucket(bucket_name)

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

    download_blob("diver-logbook-videos", video_name + ".mp4", video_name + ".mp4")

    arr = video_name.split('_')
    user_id = arr[0]
    date = arr[1]
    lat = arr[2]
    lon = (arr[3]).replace('.mp4', '')

    # get images folder path
    img_folder_path = os.path.join(os.getcwd(), "images")
    print(img_folder_path)
    results_images_folder_path = os.path.join(os.getcwd() ,folder_uuid)
    print(results_images_folder_path)

    # Create a folder to save the images
    if not os.path.exists(img_folder_path):
        os.makedirs(img_folder_path)
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
    db = firestore.Client(credentials=credentials, project=project)
    doc_ref = db.collection("DetectedFishes").document(folder_uuid)
    doc_ref.set({
        'results': json_data,
    })

    # after upload is done, delete video, images, and uuid folder
    os.remove(video_name + ".mp4")
    for file in os.listdir(img_folder_path):
        os.remove(os.path.join(img_folder_path, file))
    os.rmdir(img_folder_path)
    for file in os.listdir(folder_uuid):
        os.remove(os.path.join(folder_uuid, file))
    os.rmdir(folder_uuid)

    # JSON 파일 저장
    return jsonify({"message": "Video analysis is complete."})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)