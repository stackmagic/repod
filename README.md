repod
=====

Reclaims music files from an iPod. Licensed under the Apache License Version 2.

Features

 * Read iPod touch 4 sqlite music database
 * Copy and rename the files into a structure like: artist/year - albumname/CDdiscnumber/tracknumber - title.extension
 * Write (almost) all meta information from the database into the mp3 files (genre, album, artist, title, ...)
 * mp3 files only

TODO

 * write the rating into the mp3 files in a way other players will pick it up
 * allow to pass paths as commandline arguments
 * allow to pass filters as commandline arguments or file
 * support more filetypes

Prerequisites

 * Python 2.7
 * eyeD3 v0.7 or higher (pip install eyeD3)

Using

 * change the paths on top of repod.py (if necessary) and run the script

Developing

 * If you want to tinker with it, I strongly suggest you copy your entire ipod to a fast disk. Your test-runs will me *much* faster as compared to continuously accessing your ipod via usb.

Making a backup (or update of an existing backup) of your ipod

```
aptitude install fuse
mkdir /media/ipod /media/ipod-backup
ifuse /media/ipod
rsync -av -delete /media/ipod/* /media/ipod-backup/
```

