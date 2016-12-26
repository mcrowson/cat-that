# Cat That

Your pictures would be better with cats. Facial recognition finds faces and puts cats on them.

See live demo at [https://catthat.databeard.com](https://catthat.databeard.com)

## Purpose
This project exists to showcase several things:
 - [Zappa](https://github.com/Miserlou/Zappa): A framework for serverless Python applications.
 - [Rekognition](https://aws.amazon.com/rekognition/): AWS Service for Image recognition. 
 - Cats
 
## Overview
Images are uploaded or provided via a URL link. The image is then scanned for faces
via AWS Rekognition. For each face, a random cat face is then chosen 
and place on each face. Rekognition provides facial rotation, so the cat faces
are rotated accordingly.