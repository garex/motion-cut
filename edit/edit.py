#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import sys
from lxml import etree
from copy import copy
from collections import deque

parser = argparse.ArgumentParser(description='Montage kdenlive files.', prog="garex/motion-cut-edit")
parser.add_argument('--editor-file', required=True)
parser.add_argument('--videos', nargs = '*', required=True)
parser.add_argument('--motions', nargs = '*', required=True)

args = parser.parse_args()

editor_file = args.editor_file
videos = args.videos
motions = args.motions

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

frames = []
empty_row = [0, 0]
def frames_fill(local_frames, to_index):
    while len(local_frames) <= to_index:
        local_frames.append(copy(empty_row))

    return local_frames[to_index]

# fill frames
for i, motion in enumerate(motions):
    with open(motion) as f:
        for line in f:
            (frame_index, objects, area) = line.rstrip('\n').split(' ')
            frame_index = int(frame_index)
            frames_fill(frames, frame_index)[i] = float(objects) + float(area)

def avg(l):
    return sum(l, 0.0) / len(l)

frame_group_length = 30
# smooth_frames
for motionIndex, motion in enumerate(motions):
    frame_group = []
    for frameIndex, frame in enumerate(frames):
        frame_group.append(frame[motionIndex])
        if len(frame_group) == frame_group_length:
            average_value = avg(frame_group)
            frame_group = []
            for prevFrameIndex in range(frameIndex-frame_group_length, frameIndex):
                frames[prevFrameIndex][motionIndex] = average_value

doc = etree.parse(editor_file)

def get_producer_by_resource(video):
    return doc.xpath('//property[@name="xml"][text()="was here"]/parent::producer/property[@name="video_index"][text()!="-1"]/parent::producer/property[@name="resource"][text()="'+video+'"]/parent::producer')[0]

def get_playlist_by_producer(producer):
    return doc.xpath('//entry[@producer="'+producer.get("id")+'"]/parent::playlist')[0]

def get_first_entry_offset(playlist):
    return int(playlist.xpath("entry[1]")[0].get('in'))

def get_first_entry_out(playlist):
    return int(playlist.xpath("entry[1]")[0].get('out'))

def get_first_entry_length(playlist):
    return get_first_entry_out(playlist) - get_first_entry_offset(playlist) + 1

def clean_up_playlist(playlist):
    for bad in playlist.xpath("blank|entry"):
        bad.getparent().remove(bad)

def add_blank(playlist, length):
    playlist.append(etree.Element("blank", length=str(length)))

def add_entry(playlist, producer, start, finish):
    entry = etree.Element("entry")
    entry.set('producer', producer.get('id'))
    entry.set('in', str(start))
    entry.set('out', str(finish))
    playlist.append(entry)

offsets = []
max_entry_length = 0
max_frames_length = 0
playlists = []
producers = []
for video in videos:
    producer = get_producer_by_resource(video)
    playlist = get_playlist_by_producer(producer)
    playlists.append(playlist)
    producers.append(producer)
    offsets.append(get_first_entry_offset(playlist))
    max_entry_length = max(max_entry_length, get_first_entry_length(playlist))
    max_frames_length = max(max_frames_length, get_first_entry_out(playlist))

min_offset = min(offsets)
timeline_length = max_entry_length

frames_fill(frames, max_frames_length + max(offsets))

frames_with_offset = []
frames_fill(frames_with_offset, timeline_length - 1)

for offsetIndex, offset in enumerate(offsets):
    for frameIndex, frame in enumerate(frames_with_offset):
        frames_with_offset[frameIndex][offsetIndex] = frames[frameIndex+offset][offsetIndex]

# write some function to convert
last_frame_index = len(frames_with_offset)-1
for p, playlist in enumerate(playlists):
    eprint()
    eprint(videos[p])
    producer = producers[p]
    clean_up_playlist(playlist)
    prevAction = action = None
    prevFrameIndex = -1
    playlistFrameIndex = 0
    otherPlaylistFrameIndex = 1
    if p == 1:
        playlistFrameIndex = 1
        otherPlaylistFrameIndex = 0

    offset = offsets[p]
    for frameIndex, frame in enumerate(frames_with_offset):
        if frame[playlistFrameIndex] > frame[otherPlaylistFrameIndex] or (frame[playlistFrameIndex] == frame[otherPlaylistFrameIndex] and p == 0):
            action = 'entry'
        else:
            action = 'blank'

        if prevAction == None:
            prevAction = action
            continue

        if prevAction != action or frameIndex == last_frame_index:
            if prevAction == 'entry':
                add_entry(playlist, producer, offset+prevFrameIndex+1, offset+frameIndex)
            if prevAction == 'blank':
                add_blank(playlist, frameIndex-prevFrameIndex)

            eprint(prevAction, offset+prevFrameIndex, offset+frameIndex, frameIndex-prevFrameIndex)

            prevFrameIndex = frameIndex
            prevAction = action

doc.write(sys.stdout, pretty_print=True)
