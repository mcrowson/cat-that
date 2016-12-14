from PIL import Image

import requests

url = 'http://www.mosta2bal.com/vb/lyncache/3/22338wall.jpg'
r = requests.get(url)


def roll_to_degrees_clockwise(rollv):
    # Value given between -180 and 180. Convert to 0 to 360 counter clock-wise rotation.
    if rollv >= 0:
        res = rollv
    else:
        res = 360 + rollv
    assert 0 <= res < 360
    return res

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

# Get the input
input_image = Image.open('static/example.jpg')


# Get the cat
cats = map(Image.open, ['static/cat_pictures/cat_face2.png'])
cat = cats.pop()

# Find the face box
im_width, im_height = input_image.size
face_left = int(d[u'FaceDetails'][0][u'BoundingBox'][u'Left'] * im_width)
face_right = int(d[u'FaceDetails'][0][u'BoundingBox'][u'Width'] * im_width + face_left)
face_upper = int(d[u'FaceDetails'][0][u'BoundingBox'][u'Top'] * im_height)
face_lower = int(d[u'FaceDetails'][0][u'BoundingBox'][u'Height'] * im_height + face_upper)

# Determine face rotation
roll_val = d[u'FaceDetails'][0][u'Pose'][u'Roll']
cclock_wise_rotation = roll_to_degrees_clockwise(roll_val)
print "roatation {} degrees counter clockwise".format(cclock_wise_rotation)

# Resize the cat face to fit the box
cat_width = face_right - face_left
cat_height = face_lower - face_upper
cat_dims = (cat_width, cat_height)
sized_cat_face = cat.resize(size=cat_dims)

# Rotate the cat face to match input rotation
rolled_cat_face = sized_cat_face.rotate(cclock_wise_rotation, expand=True)
print rolled_cat_face.size

# Expand the face box to accommodate the ears poking out due to rotation
ear_pct_inc = 0.430218068535826  # the ears don't count towards the face

# Depending upon the rotation, we need to expand the face box  and rotated cat face to allow for the ears.
w, h = rolled_cat_face.size
rotation_mod = cclock_wise_rotation % 90.0
first_ext = rotation_mod/90.0
second_ext = 1.0 - first_ext
if 0 <= cclock_wise_rotation < 90:
    # Top and Left expands
    ext_h = int(h * second_ext * ear_pct_inc)
    ext_w = int(w * first_ext * ear_pct_inc)
    face_upper -= ext_h
    face_left -= ext_w

elif 90 <= cclock_wise_rotation < 180:
    # Bottom and Left expands
    ext_w = int(w * second_ext * ear_pct_inc)
    ext_h = int(h * first_ext * ear_pct_inc)
    face_left -= ext_w

elif 180 <= cclock_wise_rotation < 270:
    # Bottom and Right Expands
    ext_w = int(w * first_ext * ear_pct_inc)
    ext_h = int(h * second_ext * ear_pct_inc)

else:
    # Top and Right Expands
    ext_w = int(w * second_ext * ear_pct_inc)
    ext_h = int(h * first_ext * ear_pct_inc)
    face_upper -= ext_h


# Resize cat face to accomodate for ears
new_w = w + ext_w
new_h = h + ext_h
resized_cat_face = rolled_cat_face.resize(size=(new_w, new_h))

input_image.paste(im=resized_cat_face, box=(face_left, face_upper), mask=resized_cat_face)
input_image.show()
