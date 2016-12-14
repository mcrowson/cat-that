from flask import Flask, request, redirect, render_template, send_file
import boto3
import uuid
import imghdr
import os
from cat import CatThat
import requests
from slackclient import SlackClient
from cStringIO import StringIO
from PIL import Image


FINISHED_FOLDER = 'finished'
INPUT_KITTIES = 'stock-faces'
S3_BUCKET = 'cats.databeard.com'
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
app = Flask(__name__)

#client_id = os.environ["SLACK_CLIENT_ID"]
#client_secret = os.environ["SLACK_CLIENT_SECRET"]
#oauth_scope = os.environ["SLACK_BOT_SCOPE"]


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
    s3_url = 'https://s3.amazonaws.com/cats.databeard.com/{0!s}'.format(picture_name)
    return s3_url


@app.route('/', methods=['GET', 'POST'])
def upload_picture(event=None, context=None):
    if request.method == 'POST':
        picture_url = request.form.get('url')
        if picture_url:
            # Download the pic into tmp
            r = requests.get(picture_url, stream=True)
            if r.status_code != 200:
                print("did not get 200 response code when downloading")
                return redirect(request.url)

            file_obj = StringIO(r.content)
        elif 'file' in request.files:
            print('got a file upload')
            print(request.files['file'].filename)
            file_obj = request.files['file']
        else:
            print("did not get posted file or url in the POSt variables")
            return 'https://catthat.databeard.com/'

        if not valid_image_file(file_obj):
            print "This is not a valid image file"
            return 'https://catthat.databeard.com/'

        cat_that = CatThat()
        smaller_file = cat_that.resize_input_image(file_obj=file_obj)
        cat_faced = cat_that.add_cat_face(file_obj=smaller_file)
        if not cat_faced:
            print "couldn't put cats on this face"
            return 'https://catthat.databeard.com/'

        cat_path = upload_to_s3(file_obj=cat_faced, folder=FINISHED_FOLDER)
        print('returning {}'.format(cat_path))
        return cat_path

    return render_template('dropzone.html')


@app.route('/slack', methods=['POST', 'GET'])
def slack_receiver(event=None, context=None):
    sc = SlackClient()

    sc.api_call(
        "chat.postMessage",
        channel="#python",
        text="Hello from Python! :tada:"
    )
    return "Got here"


@app.route("/slack/begin_auth", methods=["GET"])
def pre_install(event=None, context=None):
    return '''
      <a href="https://slack.com/oauth/authorize?scope={0}&client_id={1}">
          Add to Slack
      </a>
    '''.format(oauth_scope, client_id)


@app.route("/slack/finish_auth", methods=["GET", "POST"])
def post_install(event=None, context=None):

    # Retrieve the auth code from the request params
    auth_code = request.args['code']

    # An empty string is a valid token for this request
    sc = SlackClient("")

    # Request the auth tokens from Slack
    auth_response = sc.api_call(
        "oauth.access",
        client_id=client_id,
        client_secret=client_secret,
        code=auth_code
    )
    # Save the bot token to an environmental variable or to your data store
    # for later use
    os.environ["SLACK_USER_TOKEN"] = auth_response['user_access_token']
    os.environ["SLACK_BOT_TOKEN"] = auth_response['bot']['bot_access_token']

    # Don't forget to let the user know that auth has succeeded!
    return "Auth complete!"


if __name__ == "__main__":
    app.run(debug=True)
