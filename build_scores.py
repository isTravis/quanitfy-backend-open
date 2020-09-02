from run_analysis import processVotes, calculatePercentilesAndRanks
import pymongo
from db import MongoInstance
import sys

try:
	projectInput = sys.argv[1]

	# If '_all' argument, build all projects
	if projectInput == '_all':
		allProjects = MongoInstance.client['quantify']['projects'].find()

		for project in allProjects:
			pID = project['pID']
			print "Building scores for " + pID + "..."
			processVotes(pID)
			calculatePercentilesAndRanks(pID)

	# Else, just build the specified project
	else:
		print "Building scores for " + projectInput + "..."
		processVotes(projectInput)
		calculatePercentilesAndRanks(projectInput)

except:
	print "Please specify a project pID, or use '_all' to build all projects"





