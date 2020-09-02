from run_analysis_user import processVotes, calculatePercentilesAndRanks
import pymongo
from db import MongoInstance
import sys

# try:
projectInput = sys.argv[1]
userInput = sys.argv[2]

print projectInput
print userInput

# If '_all' argument, build all projects
if projectInput == '_all' and userInput == '_all':
	allProjects = MongoInstance.client['quantify']['projects'].find()
	allUsers = MongoInstance.client['quantify']['users'].find()

	for project in allProjects:
		pID = project['pID']
		for user in allUsers:
			if 'userData' in user:
				if pID in user['userData']:
					uID = user['uID']

					print "Building scores for " + pID + " and "+ uID+"..."
					processVotes(pID,uID)
					calculatePercentilesAndRanks(pID,uID)

elif projectInput != '_all' and userInput == '_all':

	allUsers = MongoInstance.client['quantify']['users'].find()

	pID = projectInput
	for user in allUsers:
		if 'userData' in user:
			if pID in user['userData']:
				uID = user['uID']

				print "Building scores for " + pID + " and "+ uID+"..."
				processVotes(pID,uID)
				calculatePercentilesAndRanks(pID,uID)

elif projectInput == '_all' and userInput != '_all':
	allProjects = MongoInstance.client['quantify']['projects'].find()

	for project in allProjects:
		pID = project['pID']
		uID = userInput

		print "Building scores for " + pID + " and "+ uID+"..."
		processVotes(pID,uID)
		calculatePercentilesAndRanks(pID,uID)

# Else, just build the specified project
else:
	print "Building scores for " + projectInput + "..."
	processVotes(projectInput, userInput)
	calculatePercentilesAndRanks(projectInput, userInput)

# except:
# 	print "Please specify a project pID and user uID, or use '_all' to build all projects or all users"





