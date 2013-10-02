#!/usr/bin/env python
# -*- coding: utf_8 -*-

import eyed3
import os
import sqlite3 as sl
import shutil

eyed3.require("0.7")

pod = '/media/ipod-backup'
dst = '/media/ipod-music-export'

dbf = '%s/iTunes_Control/iTunes/MediaLibrary.sqlitedb' % pod
print '>>> using database file %s' % dbf

con = sl.connect(dbf)
cur = con.cursor()
cur.execute('SELECT SQLITE_VERSION()')

data = cur.fetchone()
print 'SQLite version: %s' % data

def dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d
con.row_factory = dict_factory
con.text_factory = str
cur = con.cursor()

sql = """
	SELECT
		   a.album           AS album
		, aa.album_artist    AS artist
		,  g.genre           AS genre
		, ie.YEAR            AS year
		, lk.kind            AS kind
		,  i.disc_number     AS disc_number
		,  i.track_number    AS track_number
		, ie.title           AS title
		, bl.path            AS path
		, ie.location        AS location
		, st.user_rating     AS user_rating
		, st.play_count_user AS play_count
	FROM
		  item           i
		, album          a
		, album_artist  aa
		, genre          g
		, item_extra    ie
		, location_kind lk
		, base_location bl
		, item_stats    st
	WHERE 1
		AND i.album_pid        =  a.album_pid
		AND i.album_artist_pid = aa.album_artist_pid
		AND i.genre_id         =  g.genre_id
		AND i.item_pid         = ie.item_pid
		AND i.location_kind_id = lk.location_kind_id
		AND i.base_location_id = bl.base_location_id
		AND i.item_pid         = st.item_pid
	ORDER BY
		  artist       ASC
		, year         ASC
		, album        ASC
		, disc_number  ASC
		, track_number ASC
"""

# get all items, skip some, cleanup others
cur.execute(sql)
rows = cur.fetchall()
keep = []
for row in rows:
	if row['path'] == '':
		continue
	if row['location'] == '':
		continue

	if row['artist'] == '':
		row['artist'] = 'unknown'
	if row['album'] == '':
		row['album'] = 'unknown'
	if row['title'] == '':
		row['title'] = 'unknown'

	row['artist'] = row['artist'].strip().replace('/', '-')
	row['album' ] = row['album' ].strip().replace('/', '-')
	row['title' ] = row['title' ].strip().replace('/', '-')

	keep.append(row)
	#print "{path}/{location} ({user_rating: 3d}) => {artist}/{year:04d} - {album}/CD{disc_number}/{track_number:02} - {title}.{filetype}".format( **row )

print '>>> total %d files (%d filtered)' % (len(keep), len(rows) - len(keep))

con.close()

# remove files if they already exist
shutil.rmtree(dst)

# go trough all files and
count = 0
total = len(keep)
for row in keep:

	count += 1

	row['podDir']   = pod
	row['dstDir']   = dst
	row['filetype'] = row['location'].split('.')[1]

	srcFile = "{podDir}/{path}/{location}".format( **row )
	dstDir  = "{dstDir}/{artist}/{year:04d} - {album}/CD{disc_number}".format( **row )
	dstFile = dstDir + "/{track_number:02} - {title}.{filetype}".format( **row )

	if not os.path.isfile(srcFile):
		continue

	print "[ % 7d / % 7d ] %s (%3d) => %s" % (count, total, srcFile, row['user_rating'], dstFile)

	if not os.path.isdir(dstDir):
		os.makedirs(dstDir)

	shutil.copyfile(srcFile, dstFile)

	mp3 = eyed3.load(dstFile)

	if mp3.tag == None:
		print '>>> skipping file because not an mp3'
		continue

	# get rid of all comments
	for c in mp3.tag.comments:
		mp3.tag.comments.remove(c.description)

	# stupid unicode
	mp3.tag.album      = u'%s' % row['album' ].decode('UTF-8')
	mp3.tag.artist     = u'%s' % row['artist'].decode('UTF-8')
	mp3.tag.genre.name = u'%s' % row['genre' ].decode('UTF-8')
	mp3.tag.title      = u'%s' % row['title' ].decode('UTF-8')

	# some simple numbers
	mp3.tag.disc_num   = row['disc_number']
	mp3.tag.play_count = row['play_count']

	# requires a tuple of track# and totalcount
	mp3.tag.track_num  = (row['track_number'], None)

	# it appears 0 is not valid as a year, haven't tested negative values ;)
	if row['year'] > 0:
		mp3.tag.release_date   = eyed3.core.Date(row['year'])
		mp3.tag.recording_date = eyed3.core.Date(row['year'])

	# not sure if the popularimeter stuff works as intended
	for p in mp3.tag.popularities:
		mp3.tag.popularities.remove(p.email)

	rating = int(2.55 * int(row['user_rating']))
	mp3.tag.popularities.set('rating@mp3.com', rating, row['play_count'])

	# it seems some frames can't be converted to v2.4
	for name in ('TYER', 'RGAD', 'RVAD', 'TSO2'):
		if name in mp3.tag.frame_set:
			del mp3.tag.frame_set[name]

	# commit
	mp3.tag.save(version = eyed3.id3.ID3_V2_4)
