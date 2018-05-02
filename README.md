Motion cut
==========

Cut videos from different angles automatically by motion detection.


Process
-------

For each video you provide a mask. Mask is a single frame taken from video,
where white color means "detect motion here" and black color means "ignore motion here".

First script runs for each video and generates text file with detected motions in each frame.

Second script eats editor file, videos, theirs motions and generates another editor file with tracks auto-cutted by detected motions.


How to run
----------

`docker run --volume $(pwd):/root --rm garex/motion-cut-edit --editor-file project.kdenlive --videos video1.mp4 video2.mp4 --motions video1.txt video2.txt > project.auto.kdenlive`


Supported editors
-----------------

List of supported editors:

* kdenlive


If you want to see your editor in this list you have two options: write adapter script for it or donate some money.
