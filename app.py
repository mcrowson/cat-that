from flask import Flask, request, redirect, render_template, send_file, url_for, flash, jsonify
import boto3
import uuid
import imghdr
import os
from cat import CatThat
import requests
from slackclient import SlackClient
from cStringIO import StringIO
from flask_s3 import FlaskS3


FINISHED_FOLDER = 'finished'
S3_BUCKET = 'cats.databeard.com'
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
app.config['FLASKS3_BUCKET_NAME'] = S3_BUCKET
app.config['FLASKS3_URL_STYLE'] = 'path'
app.config['FLASKS3_ACTIVE'] = False
s3 = FlaskS3(app)


def valid_image_file_odl(file_obj):
    res = imghdr.what('ignored.txt', h=file_obj.read())
    return res in ALLOWED_EXTENSIONS


def valid_image_file(file_obj):
    return '.' in file_obj.filename and \
           file_obj.filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def upload_to_s3(file_obj, folder):
    s3 = boto3.client('s3')
    picture_name = '{0!s}/{1!s}.jpg'.format(folder, uuid.uuid4())
    s3.upload_fileobj(file_obj, S3_BUCKET, picture_name, ExtraArgs={'ContentType': 'image/jpeg'})
    s3_url = 'https://s3.amazonaws.com/{0!s}/{1!s}'.format(S3_BUCKET, picture_name)
    return s3_url


@app.route('/', methods=['GET'])
def index(event=None, context=None):
    return render_template('index.html')


@app.route('/finished', methods=['GET', 'POST'])
def process(event=None, context=None):
    if request.method == 'POST':
        picture_url = request.form.get('url')
        if picture_url:

            # Download the pic into tmp
            r = requests.get(picture_url, stream=True)
            if r.status_code != 200:
                flash("We did not get 200 response code when downloading the image")
                return redirect(url_for('index'))

            file_obj = StringIO(r.content)
            result = 'redirect'

        elif 'file' in request.files:
            file_obj = request.files['file']
            if not valid_image_file(file_obj):
                flash("This is not a valid image file")
                return redirect(url_for('index'))

            result = 'json'
        else:
            flash("We did not get posted file or url in the POSt variables")
            return redirect(url_for('index'))

        cat_that = CatThat()
        cat_faced = cat_that.add_cat_face(file_obj=file_obj)
        if not cat_faced:
            flash("Couldn't put cats on this face, sorry. This this might be because no faces could be found in the image.")
            return redirect(url_for('index'))

        cat_path = upload_to_s3(file_obj=cat_faced, folder=FINISHED_FOLDER)
        print('Cat Image URL: {}'.format(cat_path))

        if result == 'redirect':
            return render_template('finished.html', data={'url': cat_path})
        else:
            return jsonify({'success': True, 'url': cat_path})

    cat_path = request.args.get('url')
    if not cat_path:
        return redirect(url_for('index'))
    return render_template('finished.html', data={'url': cat_path})

if __name__ == "__main__":
    app.run(debug=True)
