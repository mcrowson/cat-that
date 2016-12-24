from cStringIO import StringIO
import boto3
import json
from PIL import Image
import random
from botocore.exceptions import ClientError


class CatThat(object):

    @staticmethod
    def roll_to_degrees_clockwise(roll):
        # AWS Roll given between -180 and 180. Convert to 0 to 360 counter clock-wise rotation.
        assert -180 <= roll <= 180
        if roll >= 0:
            res = 360 - roll
        else:
            res = 0 - roll
        return res

    @staticmethod
    def resize_input_image(file_obj):
        """
        Resizes the input file object to something more reasonable.
        :param file_obj:
        :return:
        """
        return file_obj

    def add_cat_face(self, file_obj):
        """
        Takes a file-like object and puts a cat_image on any faces it finds.
        :param file_obj: File like object of the input image
        :return output_file: File like object of the final image
        """
        rek = boto3.client('rekognition')

        file_obj.seek(0)
        try:
            rek_results = rek.detect_faces(
                Image={
                    'Bytes': file_obj.read(),
                },
                Attributes=['DEFAULT']
            )
        except ClientError as m:
            print "got an error from AWS"
            print m.message
            return None

        if len(rek_results[u'FaceDetails']) == 0:
            # No faces in this one.
            # TODO come up with better approach
            return None

        with open('cat_list.json') as f:
            cat_options = json.load(f)

        input_image = Image.open(file_obj)

        # Add the cat face to each face in the input image
        cat_choices = [random.randint(0, len(cat_options) - 1) for i in rek_results[u'FaceDetails']]
        for face, i in zip(rek_results[u'FaceDetails'], cat_choices):
            cat_choice = cat_options[i]
            cat_image = Image.open(cat_choice['image_path'])

            # Find the face box
            im_width, im_height = input_image.size
            face_left = int(face[u'BoundingBox'][u'Left'] * im_width)
            face_right = int(face[u'BoundingBox'][u'Width'] * im_width + face_left)
            face_upper = int(face[u'BoundingBox'][u'Top'] * im_height)
            face_lower = int(face[u'BoundingBox'][u'Height'] * im_height + face_upper)

            # Determine face rotation
            roll_val = face[u'Pose'][u'Roll']
            cclock_wise_rotation = self.roll_to_degrees_clockwise(roll_val)

            # Resize the cat_image face to fit the box
            cat_width = face_right - face_left
            cat_height = face_lower - face_upper
            cat_dims = (cat_width, cat_height)
            sized_cat_face = cat_image.resize(size=cat_dims)

            # Rotate the cat_image face to match input rotation
            rolled_cat_face = sized_cat_face.rotate(cclock_wise_rotation, expand=True)

            # Expand the face box to accommodate the ears poking out due to rotation
            ear_pct_inc = float(cat_choice['ear_pct_inc'])  # the ears don't count towards the face

            # Depending upon the rotation, we need to expand the face box  and rotated cat_image face to allow for the ears.
            w, h = rolled_cat_face.size
            rotation_mod = cclock_wise_rotation % 90.0
            first_ext = rotation_mod / 90.0
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

            # Resize cat_image face to accommodate for ears
            new_w = w + ext_w
            new_h = h + ext_h
            resized_cat_face = rolled_cat_face.resize(size=(new_w, new_h))
            input_image.paste(im=resized_cat_face, box=(face_left, face_upper), mask=resized_cat_face)

        output_file = StringIO()
        input_image.save(output_file, "JPEG")
        output_file.seek(0)
        return output_file
