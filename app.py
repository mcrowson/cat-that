import os
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename
import boto3
import uuid
import imghdr
import io
import random


FINISHED_FOLDER = 'finished'
INPUT_KITTIES = 'stock-faces'
S3_BUCKET = 'cats.databeard.com'
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
app = Flask(__name__)



def add_cat_face(file_obj):
    """
    Takes a file-like object and puts a cat on any faces it finds.
    :param file_obj:
    :return:
    """
    rek = boto3.client('rekognition')
    s3 = boto3.client('s3')

    image_bytes = io.open(file_obj, mode='rb')
    rek_results = rek.detect_faces(
        Image={
            'Bytes': image_bytes,
        },
        Attributes=['DEFAULT']
    )

    if 'FaceDetails' not in rek_results:
        return None

    cat_pic = s3.download_fileobj(

    for face in rek_results['FaceDetails']:
        cat_selection = 'stock-faces/naked.jpg'


    d = {u'FaceDetails': [{u'BoundingBox': {u'Width': 0.24111111462116241, u'Top': 0.22019867599010468,
                                        u'Left': 0.4744444489479065, u'Height': 0.36092716455459595},
                       u'Landmarks': [{u'Y': 0.36806583404541016, u'X': 0.5450013279914856, u'Type': u'eyeLeft'},
                                      {u'Y': 0.35954901576042175, u'X': 0.6310957074165344, u'Type': u'eyeRight'},
                                      {u'Y': 0.41670846939086914, u'X': 0.5760032534599304, u'Type': u'nose'},
                                      {u'Y': 0.49715277552604675, u'X': 0.5669674277305603, u'Type': u'mouthLeft'},
                                      {u'Y': 0.4923478662967682, u'X': 0.6200326681137085, u'Type': u'mouthRight'}],
                       u'Pose': {u'Yaw': -13.072640419006348, u'Roll': -3.556159257888794, u'Pitch': 9.266134262084961},
                       u'Quality': {u'Sharpness': 100.0, u'Brightness': 41.504791259765625},
                       u'Confidence': 99.99169921875}], 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200,
                                                                             'RequestId': '421cc588-bdb9-11e6-ad93-3d0b4491c4f9',
                                                                             'HTTPHeaders': {
                                                                                 'date': 'Fri, 09 Dec 2016 02:43:26 GMT',
                                                                                 'x-amzn-requestid': '421cc588-bdb9-11e6-ad93-3d0b4491c4f9',
                                                                                 'content-length': '702',
                                                                                 'content-type': 'application/x-amz-json-1.1',
                                                                                 'connection': 'keep-alive'}},
     u'OrientationCorrection': u'ROTATE_0'}


    return file_obj


def get_available_cat_pictures():
    # TODO possibly just keep a list here and keep it in sync with s3 names
    s3 = boto3.client('s3')
    prefix = '{0!s}/'.format(INPUT_KITTIES)
    cat_pics = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
    if 'Contents' not in cat_pics:
        return None

    cat_keys = []
    for im in cat_pics['Contents']:
        if im['Key'] == prefix:
            continue
        cat_keys.append(im['Key'])

    return cat_keys


def valid_image_file(file_obj):
    if type(file_obj) is file:
        res = imghdr.what('ignored.txt', h=file_obj.read())
        return res in ALLOWED_EXTENSIONS


def upload_to_s3(file_obj, folder):
    s3 = boto3.client('s3')
    picture_name = '{0!s}/{0!s}.jpg'.format(folder, uuid.uuid4())
    s3.upload_fileobj(file_obj, S3_BUCKET, picture_name)
    return picture_name)


@app.route('/', methods=['GET', 'POST'])
def upload_picture(event=None, context=None):
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        file_obj = request.files['file']

        if not valid_image_file(file_obj):
            return redirect(request.url)

        cat_faced = add_cat_face(file_obj=file_obj)
        cat_path = upload_to_s3(file_obj=cat_faced, folder=FINISHED_FOLDER)
        cat_url = 'http://{0!s}/{1!s}'.format(S3_BUCKET, cat_path)

        return redirect(location=cat_url)

    return '''
           <!doctype html>
           <title>Upload new File</title>
           <h1>Upload new File</h1>
           <form action="" method=post enctype=multipart/form-data>
             <p><input type=file name=file>
                <input type=submit value=Upload>
           </form>
           '''


if __name__ == "__main__":
    app.run(debug=True)
