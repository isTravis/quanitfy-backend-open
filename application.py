#!/usr/bin/python
'''
QUANTIFY Restful API
'''
import json
import time

from flask import Flask, request, abort, redirect, Response, jsonify
from flask.ext.restful import Resource, Api, reqparse
# from werkzeug.contrib.fixers import ProxyFix

from db import MongoInstance
from bson.objectid import ObjectId

application = Flask(__name__)
api = Api(application)

PORT = 8888

# cookieUserName = ''

# TODO: Write unit tests
# TODO: Ensure arguments have equal length
# TODO: Use Marshaling (includes formatting) or mongoDB exclusion?
# TODO: Return status codes
# If the pID is not found, return an error saying so.

#!!TODO Simple query for total number of votes on project
#!!TODO Simple query for total number of content. Perhaps a simple project-status query, that returns all these nice things.

#!!!! For quantify frontend, need to make an API endpoint that can only be access from quant.media.

@application.before_request
def option_autoreply():
	""" Always reply 200 on OPTIONS request """
	if request.method == 'OPTIONS':
		resp = application.make_default_options_response()

		headers = None
		if 'ACCESS_CONTROL_REQUEST_HEADERS' in request.headers:
			headers = request.headers['ACCESS_CONTROL_REQUEST_HEADERS']

		h = resp.headers

		h['Access-Control-Allow-Origin'] = request.headers['Origin']# Allow the origin which made the XHR
		h['Access-Control-Allow-Methods'] = request.headers['Access-Control-Request-Method']# Allow the actual method
		h['Access-Control-Max-Age'] = "10"# Allow for 10 seconds

		if headers is not None:        # We also keep current headers 
			h['Access-Control-Allow-Headers'] = headers

		return resp

@application.after_request
def set_allow_origin(resp):
	""" Set origin for GET, POST, PUT, DELETE requests """
	h = resp.headers
	if request.method != 'OPTIONS' and 'Origin' in request.headers: # Allow crossdomain for other HTTP Verbs
		h['Access-Control-Allow-Origin'] = request.headers['Origin']
		
	h['Access-Control-Allow-Credentials'] = 'true'
	return resp




############################
# Authentication Decorator
############################
# Decorator function validating application keys
def public_key(fn):
	def decorated_fn(*args, **kwargs):
		# print request.form['key']
		# print "Request from %s" % (request.args.get('key'))
		# print "Request for %s" % (request.args.get('pID'))
		pID = request.args.get('pID')
		if pID == None: # If the pID is in the payload of a POST, rather than the url args
			pID = request.form['pID']
		key = request.args.get('key')
		if key == None: # If the key is in the payload of a POST, rather than the url args
			key = request.form['key']

		isValid = MongoInstance.isValidPublic(pID,key)
		if isValid:
			return fn(*args, **kwargs)
		else:
			return "Invalid Key"
	return decorated_fn

def admin_key(fn):
	def decorated_fn(*args, **kwargs):
		# print "Request from %s" % (request.args.get('key'))
		# print "Request for %s" % (request.args.get('pID'))
		pID = request.args.get('pID')
		if pID == None: # If the pID is in the payload of a POST, rather than the url args
			pID = request.form['pID']
		key = request.args.get('key')
		if key == None: # If the key is in the payload of a POST, rather than the url args
			key = request.form['key']
		isValid = MongoInstance.isValidAdmin(pID,key)
		if isValid:
			return fn(*args, **kwargs)
		else:
			return "Invalid Key"
	return decorated_fn

# class AuthenticationError(Exception): pass



############################
# Endpoint Specifications
############################

############################
# Project
############################

projectGetParser = reqparse.RequestParser()
projectGetParser.add_argument('pID', type=str, action='append', required=True)
projectGetParser.add_argument('key', type=str, required=True)

projectPutParser = reqparse.RequestParser()
projectPutParser.add_argument('pID', type=str, action='append', required=True)
projectPutParser.add_argument('projectTitle', type=str, action='append', required=True)
projectPutParser.add_argument('ownerEmail', type=str, action='append', required=True)
projectPutParser.add_argument('description', type=str, action='append', required=True)
projectPutParser.add_argument('ownerFirstName', type=str, action='append', required=True)
projectPutParser.add_argument('ownerLastName', type=str, action='append', required=True)
projectPutParser.add_argument('key', type=str, required=True)

projectPostParser = reqparse.RequestParser()
projectPostParser.add_argument('projectTitle', type=str, action='append', required=True)
projectPostParser.add_argument('ownerEmail', type=str, action='append', required=True)
projectPostParser.add_argument('description', type=str, action='append', required=True)
projectPostParser.add_argument('ownerFirstName', type=str, action='append', required=True)
projectPostParser.add_argument('ownerLastName', type=str, action='append', required=True)


projectDeleteParser = reqparse.RequestParser()
projectDeleteParser.add_argument('pID', type=str, action='append', required=True)
projectDeleteParser.add_argument('key', type=str, required=True)

class Project(Resource):
	@public_key
	def get(self):
		args = projectGetParser.parse_args()
		pIDs = args.get('pID')
		return [ MongoInstance.getProject(pID) for pID in pIDs ]
	@admin_key
	def put(self):
		args = projectPutParser.parse_args()
		pIDs = args.get('pID')
		description = args.get('description')
		project_titles  = args.get('projectTitle')
		owner_emails = args.get('ownerEmail')
		owner_first_names = args.get('ownerFirstName')
		owner_last_names = args.get('ownerLastName')
		params = zip(pIDs, project_titles, owner_emails, owner_first_names, owner_last_names, description)
		return [ MongoInstance.putProject(pID,project_title=project_title, owner_email=owner_email, owner_first_name=owner_first_name, owner_last_name=owner_last_name, description=description) \
			for (pID, project_title, owner_email, owner_first_name, owner_last_name, description) in params]
	def post(self):
		args = projectPostParser.parse_args()
		project_titles = args.get('projectTitle')
		description = args.get('description')
		owner_emails = args.get('ownerEmail')
		owner_first_names = args.get('ownerFirstName')
		owner_last_names = args.get('ownerLastName')
		params = zip(project_titles, owner_emails, owner_first_names, owner_last_names, description)
		return [ MongoInstance.postProject(project_title=project_title, owner_email=owner_email, owner_first_name=owner_first_name, owner_last_name=owner_last_name, description=description) \
			for (project_title, owner_email, owner_first_name, owner_last_name, description) in params ]
	@admin_key
	def delete(self):
		args = projectDeleteParser.parse_args()
		pIDs = args.get('pID')
		return [ MongoInstance.deleteProject(pID) for pID in pIDs]



api.add_resource(Project, '/api/project')

############################
# Content
############################

contentGetParser = reqparse.RequestParser()
contentGetParser.add_argument('cID', type=str, action='append', required=True)
contentGetParser.add_argument('pID', type=str, required=True)
contentGetParser.add_argument('key', type=str, required=True)

contentPostParser = reqparse.RequestParser()
contentPostParser.add_argument('content', type=str, action='append', required=True)
contentPostParser.add_argument('content_type', type=str, action='append', required=True)
contentPostParser.add_argument('content_data', type=str, action='append', required=True)
contentPostParser.add_argument('pID', type=str, required=True)
contentPostParser.add_argument('key', type=str, required=True)

contentDeleteParser = reqparse.RequestParser()
contentDeleteParser.add_argument('cID', type=str, action='append', required=True)
contentDeleteParser.add_argument('pID', type=str, required=True)
contentDeleteParser.add_argument('key', type=str, required=True)

class Content(Resource):
	@public_key
	def get(self):
		args = contentGetParser.parse_args()
		cIDs = args.get('cID')
		pID = args.get('pID')
		return MongoInstance.getThing(pID, 'content', cIDs)
	@admin_key
	def post(self):
		args = contentPostParser.parse_args()
		contents = args.get('content')
		content_types = args.get('content_type')
		content_datas = args.get('content_data')
		pID = args.get('pID')
		docs = zip(contents, content_types, content_datas)
		# print "well I'm here"
		return [ MongoInstance.postContent(pID, content=content, content_type=content_type, content_data=content_data) \
			for (content, content_type, content_data) in docs]
	@admin_key
	def delete(self):
		args = contentDeleteParser.parse_args()
		cIDs = args.get('cID')
		pID = args.get('pID')
		return MongoInstance.deleteThing(pID, 'content', cIDs)

api.add_resource(Content, '/api/content')


############################
# ContentByIndex
############################

contentByIndexGetParser = reqparse.RequestParser()
contentByIndexGetParser.add_argument('index', type=str, action='append', required=True)
contentByIndexGetParser.add_argument('pID', type=str, required=True)
contentByIndexGetParser.add_argument('key', type=str, required=True)

class ContentByIndex(Resource):
	@public_key
	def get(self):
		args = contentByIndexGetParser.parse_args()
		index = args.get('index')
		pID = args.get('pID')
		return MongoInstance.getContentByIndex(pID, index)

api.add_resource(ContentByIndex, '/api/contentbyindex')

############################
# Metric
############################

# TODO: Validate equal length of passed arguments
metricGetParser = reqparse.RequestParser()
metricGetParser.add_argument('mID', type=str, action='append', required=True)
metricGetParser.add_argument('pID', type=str, required=True)
metricGetParser.add_argument('key', type=str, required=True)

metricPostParser = reqparse.RequestParser()
metricPostParser.add_argument('name', type=str, action='append', required=True)
metricPostParser.add_argument('prefix', type=str, action='append', required=True)
metricPostParser.add_argument('pID', type=str, required=True)
metricPostParser.add_argument('key', type=str, required=True)

metricDeleteParser = reqparse.RequestParser()
metricDeleteParser.add_argument('mID', type=str, action='append', required=True)
metricDeleteParser.add_argument('pID', type=str, required=True)
metricDeleteParser.add_argument('key', type=str, required=True)

class Metric(Resource):
	@public_key
	def get(self):
		args = metricGetParser.parse_args()
		mIDs = args.get('mID')
		pID = args.get('pID')
		return MongoInstance.getThing(pID, 'metrics', mIDs)
	@admin_key
	def post(self):
		args = metricPostParser.parse_args()
		names = args.get('name')
		prefixes = args.get('prefix')
		pID = args.get('pID')
		docs = zip(names, prefixes)
		print docs
		return [ MongoInstance.postMetric(pID, metric_name=name, metric_prefix=prefix) \
			for (name, prefix) in docs]
	@admin_key
	def delete(self):
		args = metricDeleteParser.parse_args()
		mIDs = args.get('mID')
		pID = args.get('pID')
		return MongoInstance.deleteThing(pID, 'metrics', mIDs)
	

api.add_resource(Metric, '/api/metric')

# ############################
# # Owner (top-level QUANTIFY users)
# ############################

# ownerGetParser = reqparse.RequestParser()
# ownerGetParser.add_argument('owner_data', type=str, required=True)

# ownerPutParser = reqparse.RequestParser()
# ownerPutParser.add_argument('uID', type=str, action='append', required=True)
# ownerPutParser.add_argument('owner_data', type=str, action='append', required=True)
# ownerPutParser.add_argument('pID', type=str, required=True)
# ownerPutParser.add_argument('key', type=str, required=True)

# ownerPostParser = reqparse.RequestParser()
# ownerPostParser.add_argument('owner_data', type=str, required=True)
# # ownerPostParser.add_argument('key', type=str, required=True)

# ownerDeleteParser = reqparse.RequestParser()
# ownerDeleteParser.add_argument('uID', type=str, action='append', required=True)
# ownerDeleteParser.add_argument('pID', type=str, required=True)
# ownerDeleteParser.add_argument('key', type=str, required=True)


# class Owner(Resource):
# 	# Currently used for logging in (maybe should have its own endpoint)
# 	def get(self):
# 		args = ownerGetParser.parse_args()
# 		owner_data = args.get('owner_data')
# 		print "GET", owner_data

# 		return MongoInstance.getThing('', 'owners', owner_data)
# 	def put(self): 
# 		args = userPutParser.parse_args()
# 		uIDs = args.get('uID')
# 		user_datas = args.get('user_data')
# 		pID = args.get('pID')
# 		return MongoInstance.postThing(pID, 'owners', uIDs=uIDS, user_data=user_datas)
# 	def post(self):
# 		args = ownerPostParser.parse_args()
# 		owner_data = args.get('owner_data')

# 		return MongoInstance.postThing('', 'owners', owner_data=owner_data)
# 	def delete(self):
# 		args = userDeleteParser.parse_args()
# 		uIDs = args.get('uID')
# 		pID = args.get('pID')
# 		return MongoInstance.deleteThing(pID, 'owners', uIDs)

# api.add_resource(Owner, '/api/owner')

# userGetParser = reqparse.RequestParser()
# userGetParser.add_argument('uID', type=str, action='append', required=True)
# userGetParser.add_argument('pID', type=str, required=True)
# userGetParser.add_argument('key', type=str, required=True)

# userPutParser = reqparse.RequestParser()
# userPutParser.add_argument('uID', type=str, action='append', required=True)
# userPutParser.add_argument('user_data', type=str, action='append', required=True)
# userPutParser.add_argument('pID', type=str, required=True)
# userPutParser.add_argument('key', type=str, required=True)

# userPostParser = reqparse.RequestParser()
# userPostParser.add_argument('', type=str, action='append', required=True)
# userPostParser.add_argument('pID', type=str, required=True)
# userPostParser.add_argument('key', type=str, required=True)

# userDeleteParser = reqparse.RequestParser()
# userDeleteParser.add_argument('uID', type=str, action='append', required=True)
# userDeleteParser.add_argument('pID', type=str, required=True)
# userDeleteParser.add_argument('key', type=str, required=True)


# class User(Resource):
# 	def get(self):
# 		args = userGetParser.parse_args()
# 		uIDs = args.get('uID')
# 		pID = args.get('pID')
# 		return MongoInstance.getThing(pID, 'users', uIDs)
# 	def put(self):
# 		args = userPutParser.parse_args()
# 		uIDs = args.get('uID')
# 		user_datas = args.get('user_data')
# 		pID = args.get('pID')
# 		return MongoInstance.postThing(pID, 'user', uIDs=uIDS, user_data=user_datas)
# 	def post(self):
# 		args = userPostParser.parse_args()
# 		print 'POST:', args
# 		user_datas = args.get('user_data')
# 		pID = args.get('pID')

# 		return [ MongoInstance.postThing(pID, 'user', user_data=user_data) \
# 		    for user_data in user_datas]
# 	def delete(self):
# 		args = userDeleteParser.parse_args()
# 		uIDs = args.get('uID')
# 		pID = args.get('pID')
# 		return MongoInstance.deleteThing(pID, 'users', uIDs)

# api.add_resource(User, '/api/user')

############################
# Vote
############################

voteGetParser = reqparse.RequestParser()
voteGetParser.add_argument('vID', type=str, action='append', required=True)
voteGetParser.add_argument('pID', type=str, required=True)
voteGetParser.add_argument('key', type=str, required=True)

votePostParser = reqparse.RequestParser()
votePostParser.add_argument('vote_result', type=str, action='append', required=True)
# vote_result must be of format: {cID1: rank, cID2: rank, cID3: rank}. Lower rank is better
votePostParser.add_argument('vote_data', type=str, action='append', required=True)
votePostParser.add_argument('voter_ip', type=str)
votePostParser.add_argument('mID', type=str, required=True)
votePostParser.add_argument('uID', type=str, required=True)
votePostParser.add_argument('pID', type=str, required=True)
votePostParser.add_argument('key', type=str, required=True)

class Vote(Resource):
	@public_key
	def get(self):
		args = voteGetParser.parse_args()
		vIDs = args.get('vID')
		pID = args.get('pID')
		return MongoInstance.getThing(pID, 'votes', vIDs)
	@public_key
	def post(self):

		args = votePostParser.parse_args()
		vote_results = args.get('vote_result')
		vote_datas = args.get('vote_data')
		voter_ip = args.get('voter_ip')
		mID = args.get('mID')
		uID = args.get('uID')
		pID = args.get('pID')
		docs = zip(vote_results, vote_datas)
		return [ MongoInstance.postVote(pID, mID=mID, vote_result=vote_result, voter_ip=voter_ip, uID=uID, vote_data=vote_data) \
			for (vote_result, vote_data) in docs]

api.add_resource(Vote, '/api/vote')

############################
# User_Votes
############################

userVoteGetParser = reqparse.RequestParser()
userVoteGetParser.add_argument('uID', type=str, required=True)
userVoteGetParser.add_argument('limit', type=str, default='1')
userVoteGetParser.add_argument('pID', type=str, required=True)
userVoteGetParser.add_argument('key', type=str, required=True)



class UserVotes(Resource):
	@public_key
	def get(self):
		args = userVoteGetParser.parse_args()
		uID = args.get('uID')
		limit = args.get('limit')
		pID = args.get('pID')
		return MongoInstance.getUserVotes(pID, uID, limit)

api.add_resource(UserVotes, '/api/uservotes')



############################
# Keys
############################

keyGetParser = reqparse.RequestParser()
keyGetParser.add_argument('kID', type=str, action='append', required=True)
keyGetParser.add_argument('pID', type=str, required=True)
keyGetParser.add_argument('key', type=str, required=True)

keyPostParser = reqparse.RequestParser()
keyPostParser.add_argument('is_admin', type=str, action='append', required=True)
keyPostParser.add_argument('pID', type=str, required=True)
keyPostParser.add_argument('key', type=str, required=True)

keyDeleteParser = reqparse.RequestParser()
keyDeleteParser.add_argument('kID', type=str, action='append', required=True)
keyDeleteParser.add_argument('pID', type=str, required=True)
keyDeleteParser.add_argument('key', type=str, required=True)

class Key(Resource):
	@admin_key
	def get(self):
		args = keyGetParser.parse_args()
		kIDs = args.get('kID')
		pID = args.get('pID')
		return MongoInstance.getThing(pID, 'keys', kIDs)
	@admin_key
	def post(self):
		args = keyPostParser.parse_args()
		is_admins = args.get('is_admin')
		pID = args.get('pID')
		return [ MongoInstance.postThing(pID, 'key', is_admin=is_admin) \
			for is_admin in is_admins]
	@admin_key
	def delete(self):
		args = keyDeleteParser.parse_args()
		kIDs = args.get('kID')
		pID = args.get('pID')
		return MongoInstance.deleteThing(pID, 'keys', kIDs)

api.add_resource(Key, '/api/key')

############################
# Contestants
############################

contestantsParser = reqparse.RequestParser()
contestantsParser.add_argument('num_desired_contestants', type=int, default=2)
contestantsParser.add_argument('mID', type=str, required=True)
contestantsParser.add_argument('pID', type=str, required=True)
contestantsParser.add_argument('mode', type=str, required=True)
contestantsParser.add_argument('key', type=str, required=True)
class Contestants(Resource):
	@public_key
	def get(self):
		args = contestantsParser.parse_args()
		num_desired_contestants = args.get('num_desired_contestants')
		mID = args.get('mID')
		pID = args.get('pID')
		mode = args.get('mode')
		key = args.get('key')
		return MongoInstance.getContestants(pID, mID, num_desired_contestants,mode)


api.add_resource(Contestants, '/api/contestants')

############################
# User_Contestants
############################

usercontestantsParser = reqparse.RequestParser()
usercontestantsParser.add_argument('num_desired_contestants', type=int, default=2)
usercontestantsParser.add_argument('mID', type=str, required=True)
usercontestantsParser.add_argument('uID', type=str, required=True)
usercontestantsParser.add_argument('pID', type=str, required=True)
usercontestantsParser.add_argument('mode', type=str, required=True)
usercontestantsParser.add_argument('key', type=str, required=True)
class UserContestants(Resource):
	@public_key
	def get(self):
		args = usercontestantsParser.parse_args()
		num_desired_contestants = args.get('num_desired_contestants')
		mID = args.get('mID')
		uID = args.get('uID')
		pID = args.get('pID')
		mode = args.get('mode')
		key = args.get('key')
		return MongoInstance.getContestants_user(pID, uID, mID, num_desired_contestants,mode)


api.add_resource(UserContestants, '/api/user_contestants')



############################
# Scores
############################

scoresParser = reqparse.RequestParser()
scoresParser.add_argument('cID', type=str, action='append', required=True)
scoresParser.add_argument('pID', type=str, required=True)
scoresParser.add_argument('key', type=str, required=True)
class Scores(Resource):
	@public_key
	def get(self):
		args = scoresParser.parse_args()
		cIDs = args.get('cID')
		pID = args.get('pID')
		key = args.get('key')
		return MongoInstance.getScores(pID, cIDs)

api.add_resource(Scores, '/api/scores')

############################
# User_Scores
############################

userscoresParser = reqparse.RequestParser()
userscoresParser.add_argument('cID', type=str, action='append', required=True)
userscoresParser.add_argument('pID', type=str, required=True)
userscoresParser.add_argument('key', type=str, required=True)
class UserScores(Resource):
	@public_key
	def get(self):
		args = userscoresParser.parse_args()
		cIDs = args.get('cID')
		uID = args.get('uID')
		pID = args.get('pID')
		key = args.get('key')
		return MongoInstance.getScores_user(pID, uID, cIDs)

api.add_resource(UserScores, '/api/user_scores')

############################
# Results
############################

resultsParser = reqparse.RequestParser()
resultsParser.add_argument('mID', type=str, required=True)
# resultsParser.add_argument('sort', type=int, default=1, choices=[-1,1]) #Choices doesn't seem to be working, can't figure out what's funky
resultsParser.add_argument('sort', type=int, default=1)
resultsParser.add_argument('skip', type=int, default=0)
resultsParser.add_argument('limit', type=int, default=10)
resultsParser.add_argument('pID', type=str, required=True)
resultsParser.add_argument('key', type=str, required=True)
class Results(Resource):
	@public_key
	def get(self):
		args = resultsParser.parse_args()
		mID = args.get('mID')
		sort = args.get('sort')
		skip = args.get('skip')
		limit = args.get('limit')
		pID = args.get('pID')
		return MongoInstance.getResults(pID, mID, sort, skip, limit)

api.add_resource(Results, '/api/results')

############################
# User_Results
############################

userresultsParser = reqparse.RequestParser()
userresultsParser.add_argument('mID', type=str, required=True)
# resultsParser.add_argument('sort', type=int, default=1, choices=[-1,1]) #Choices doesn't seem to be working, can't figure out what's funky
userresultsParser.add_argument('sort', type=int, default=1)
userresultsParser.add_argument('skip', type=int, default=0)
userresultsParser.add_argument('limit', type=int, default=10)
userresultsParser.add_argument('uID', type=str, required=True)
userresultsParser.add_argument('pID', type=str, required=True)
userresultsParser.add_argument('key', type=str, required=True)
class UserResults(Resource):
	@public_key
	def get(self):
		args = userresultsParser.parse_args()
		mID = args.get('mID')
		sort = args.get('sort')
		skip = args.get('skip')
		limit = args.get('limit')
		uID = args.get('uID')
		pID = args.get('pID')
		return MongoInstance.getResults_user(pID, uID, mID, sort, skip, limit)

api.add_resource(UserResults, '/api/user_results')

############################
# DisplayMetrics
############################

displayMetricsParser = reqparse.RequestParser()
displayMetricsParser.add_argument('mode', type=str, required=True)
displayMetricsParser.add_argument('limit', type=int, default=1)
displayMetricsParser.add_argument('pID', type=str, required=True)
displayMetricsParser.add_argument('key', type=str, required=True)
class DisplayMetrics(Resource):
	@public_key
	def get(self):
		args = displayMetricsParser.parse_args()
		mode = args.get('mode')
		limit = args.get('limit')
		pID = args.get('pID')
		# global cookieUserName
		return MongoInstance.getDisplayMetrics(pID, mode, limit)

api.add_resource(DisplayMetrics, '/api/displaymetrics')

############################
# Search
############################

searchParser = reqparse.RequestParser()
searchParser.add_argument('mID', type=str, required=True)
searchParser.add_argument('metric_score', type=str, required=True)
# Assuming metric score has the following format: metricscore=('mID',0.2)
searchParser.add_argument('skip', type=int, default=0)
searchParser.add_argument('limit', type=int, default=10)
searchParser.add_argument('pID', type=str, required=True)
searchParser.add_argument('key', type=str, required=True)
class Search(Resource):
	@public_key
	def get(self):
		args = searchParser.parse_args()
		mIDs = args.get('mID').replace("[","").replace("]","").split(',') # Converts string 'array' into 
		metric_scores = args.get('metric_score').replace("[","").replace("]","").split(',')
		skip = args.get('skip')
		limit = args.get('limit')
		pID = args.get('pID')
		key = args.get('key')
		# print pID, metricScore, skip, limit
		search_vector = zip(mIDs, metric_scores)
		print search_vector
		
		return MongoInstance.getSearch(pID, search_vector, skip, limit)

api.add_resource(Search, '/api/search')

############################
# User_Search
############################

usersearchParser = reqparse.RequestParser()
usersearchParser.add_argument('mID', type=str, required=True)
usersearchParser.add_argument('metric_score', type=str, required=True)
# Assuming metric score has the following format: metricscore=('mID',0.2)
usersearchParser.add_argument('skip', type=int, default=0)
usersearchParser.add_argument('limit', type=int, default=10)
usersearchParser.add_argument('uID', type=str, required=True)
usersearchParser.add_argument('pID', type=str, required=True)
usersearchParser.add_argument('key', type=str, required=True)
class UserSearch(Resource):
	@public_key
	def get(self):
		args = usersearchParser.parse_args()
		mIDs = args.get('mID').replace("[","").replace("]","").split(',') # Converts string 'array' into 
		metric_scores = args.get('metric_score').replace("[","").replace("]","").split(',')
		skip = args.get('skip')
		limit = args.get('limit')
		uID = args.get('uID')
		pID = args.get('pID')
		key = args.get('key')
		# print pID, metricScore, skip, limit
		search_vector = zip(mIDs, metric_scores)
		print search_vector
		
		return MongoInstance.getSearch_user(pID, uID, search_vector, skip, limit)

api.add_resource(UserSearch, '/api/user_search')




############################
# projectStats
############################

projectStatsParser = reqparse.RequestParser()
projectStatsParser.add_argument('pID', type=str, required=True)
projectStatsParser.add_argument('key', type=str, required=True)
class ProjectStats(Resource):
	@public_key
	def get(self):
		args = projectStatsParser.parse_args()
		pID = args.get('pID')
		return MongoInstance.getProjectStats(pID)

api.add_resource(ProjectStats, '/api/projectstats')

############################
# projectKeys
############################

projectKeysParser = reqparse.RequestParser()
projectKeysParser.add_argument('pID', type=str, required=True)
projectKeysParser.add_argument('user', type=str, required=True)
projectKeysParser.add_argument('pwHash', type=str, required=True)
# projectKeysParser.add_argument('key', type=str, required=True)
class ProjectKeys(Resource):
	def get(self):
		args = projectKeysParser.parse_args()
		pID = args.get('pID')
		user = args.get('user')
		pwHash = args.get('pwHash')
		return MongoInstance.getProjectKeys(pID,user,pwHash)

api.add_resource(ProjectKeys, '/api/projectkeys')

############################
# ProjectNameAvailable
############################

projectNameAvailableParser = reqparse.RequestParser()
projectNameAvailableParser.add_argument('pID', type=str, required=True)
# projectNameAvailableParser.add_argument('key', type=str, required=True)
class ProjectNameAvailable(Resource):
	def get(self):
		args = projectNameAvailableParser.parse_args()
		pID = args.get('pID')
		return not MongoInstance.validPID(pID)

api.add_resource(ProjectNameAvailable, '/api/projectnameavailable')

# ############################
# # ScoresAvailable
# ############################

# scoresAvailableParser = reqparse.RequestParser()
# scoresAvailableParser.add_argument('pID', type=str, required=True)
# # scoresAvailableParser.add_argument('key', type=str, required=True)
# class ScoresAvailable(Resource):
# 	def get(self):
# 		args = scoresAvailableParser.parse_args()
# 		pID = args.get('pID')
# 		return MongoInstance.scoresAvailable(pID)

# api.add_resource(ScoresAvailable, '/api/scoresavailable')

############################
# Account
############################

accountParser = reqparse.RequestParser()
accountParser.add_argument('user', type=str, required=True)
accountParser.add_argument('pwHash', type=str, required=True)
# accountParser.add_argument('key', type=str, required=True)
class account(Resource):
	def get(self):
		args = accountParser.parse_args()
		user = args.get('user')
		pwHash = args.get('pwHash')
		return MongoInstance.getAccount(user, pwHash)

	def post(self):
		args = accountParser.parse_args()
		user = args.get('user')
		pwHash = args.get('pwHash')
		return MongoInstance.postAccount(user, pwHash)

		
		
	def delete(self):
		args = accountParser.parse_args()
		user = args.get('user')
		pwHash = args.get('pwHash')
		return MongoInstance.deleteAccount(user, pwHash)

api.add_resource(account, '/api/account')

############################
# AccountData
############################
acountDataGetParser = reqparse.RequestParser()
acountDataGetParser.add_argument('user', type=str, required=True)
acountDataGetParser.add_argument('pwHash', type=str, required=True)
# acountDataGetParser.add_argument('key', type=str, required=True)

acountDataPostParser = reqparse.RequestParser()
acountDataPostParser.add_argument('user', type=str, required=True)
acountDataPostParser.add_argument('pwHash', type=str, required=True)
acountDataPostParser.add_argument('account_data', type=str, required=True)
# acountDataPostParser.add_argument('key', type=str, required=True)
class accountData(Resource):
	def get(self):
		args = acountDataGetParser.parse_args()
		user = args.get('user')
		pwHash = args.get('pwHash')
		return MongoInstance.getAccountData(user, pwHash)

	def post(self):
		args = acountDataPostParser.parse_args()
		user = args.get('user')
		pwHash = args.get('pwHash')
		account_data = args.get('account_data')
		return MongoInstance.postAccountData(user, pwHash, account_data)

	def delete(self):
		args = acountDataGetParser.parse_args()
		user = args.get('user')
		pwHash = args.get('pwHash')
		account_data = '{"projects":[]}'
		return MongoInstance.postAccountData(user, pwHash, account_data)

api.add_resource(accountData, '/api/accountdata')

############################
# CheckUserCookie
############################
class checkUserCookie(Resource):
	def get(self):

		try:
			cookies = dict([e.split('=') for e in request.headers['Cookie'].replace(' ', '').split(';')])
			print cookies
			uID = cookies['qnt_uID']
			return [{'uID':uID}]
		except:
			return [{'uID':''}]

		# if cookieUserName == '':
		# 	return [{'uID':''}]

		cookies = dict([e.split('=') for e in cookieUserName.replace(' ', '').split(';')])
		# print cookies
		# if 'qnt_uID' in cookies:
		# 	return [{'uID':cookies['qnt_uID']}]
		# else:
		# 	return [{'uID':''}]

api.add_resource(checkUserCookie, '/api/checkusercookie')




############################
# CreateUser
############################
createUserParser = reqparse.RequestParser()
createUserParser.add_argument('pID', type=str, required=True)
createUserParser.add_argument('key', type=str, required=True)
class CreateUser(Resource):
	@public_key
	def post(self):
		args = createUserParser.parse_args()
		pID = args.get('pID')
		uID = MongoInstance.createUser(pID)[0]['uID']

		resp = jsonify({'uID':uID})
		resp.status_code = 200
		# Need to set expires to a long long time for the cookie
		resp.set_cookie('qnt_uID',value=uID, expires=2577836800)

		return resp


api.add_resource(CreateUser, '/api/createuser')



# This is no good, need a full-on get/post/push user setup. 
############################
# UserData
############################
userDataGetParser = reqparse.RequestParser()
userDataGetParser.add_argument('pID', type=str, required=True)
userDataGetParser.add_argument('uID', type=str, required=True)
userDataGetParser.add_argument('key', type=str, required=True)

userDataPutParser = reqparse.RequestParser()
userDataPutParser.add_argument('pID', type=str, required=True)
userDataPutParser.add_argument('uID', type=str, required=True)
userDataPutParser.add_argument('user_data', type=str, required=True)
userDataPutParser.add_argument('key', type=str, required=True)
class UserData(Resource):
	@public_key
	def get(self):
		args = userDataGetParser.parse_args()
		pID = args.get('pID')
		uID = args.get('uID')
		return MongoInstance.getUserData(pID, uID)
	@public_key
	def post(self):
		args = userDataPutParser.parse_args()
		pID = args.get('pID')
		uID = args.get('uID')
		user_data = args.get('user_data')
		return MongoInstance.putUserData(pID, uID, user_data)

api.add_resource(UserData, '/api/userdata')



############################
# BuildScores
############################
buildScoresParser = reqparse.RequestParser()
buildScoresParser.add_argument('pID', type=str, required=True)
buildScoresParser.add_argument('uID', type=str, default='')
buildScoresParser.add_argument('key', type=str, required=True)


class BuildScores(Resource):
	@public_key
	def get(self):
		args = buildScoresParser.parse_args()
		pID = args.get('pID')
		uID = args.get('uID')
		return MongoInstance.buildScores(pID, uID)

api.add_resource(BuildScores, '/api/buildscores')


# Get IP!
class IP(Resource):
	def get(self):
		try:
			if request.headers.getlist("X-Forwarded-For"):
				ip = request.headers.getlist("X-Forwarded-For")
				return ip
			else:
				ip = request.remote_addr
				return ip
			# print ip
		except:
			return "dun goofed"
		# print request.access_route
		# print request.remote_addr
		# print request.headers.getlist("X-Forwarded-For")
		# # return json.dumps(request)
		# print ProxyFix(application.wsgi_app)
api.add_resource(IP, '/api/ip')




if __name__ == '__main__':
	# application.run(debug=True, host='0.0.0.0', port=PORT)
	application.run(host = '0.0.0.0', debug=False)
	# application.run(debug="true", port=PORT)
