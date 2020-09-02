import pymongo
import json

import time



connection = pymongo.Connection(host='127.0.0.1', port=27017)

try:
	db = connection.gifgif

except:
	print "Can't find DB"

c_metrics = db.metrics

print "Testing Find"
x = c_metrics.find({})
for item in x:
	print item

print "Testing Find One"
print c_metrics.find_one({'metric': 'pride'})