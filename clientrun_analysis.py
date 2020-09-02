from time import time
import sys, os
import pymongo
# from db import MongoInstance
from trueskill import Rating, TrueSkill
import numpy as np
import pandas as pd

def getmIDs(MongoInstance,pID):
    mIDs = []
    metrics = MongoInstance.client[pID]['metrics'].find()
    for metric in metrics:
        mIDs.append(str(metric['_id']))
    return mIDs


# Do all the trueSkill analysis across all votes. Update db
def processVotes(MongoInstance,pID):
  # print 'Processing past votes of ' + pID

  votes = MongoInstance.client[pID]['votes'].find({'flagged': False}).sort('submit_time', 1)
  # print votes.count(), 'un-calculated votes found in the DB'
  vote_count = 0
  # start_time = time()
  for vote in votes:
    print vote
    vote_count += 1
    # print vote_count

    mID = str(vote['mID'])
    vote_result = vote['vote_result']
    
    contestants = []
    rankings = []


    for cID in vote_result:
      if MongoInstance.client[pID]['scores'].find_one({'cID':cID}) == None:
        
        MongoInstance.initialize_score(pID,cID)

      scoreDoc = MongoInstance.client[pID]['scores'].find_one({'cID':cID})

      mu = scoreDoc['parameters'][mID]['mu']
      sigma = scoreDoc['parameters'][mID]['sigma']
      
      contestants.append({cID:Rating(mu,sigma)})
      rankings.append(vote_result[cID])
    # print rankings
    updated_scores = TrueSkill().rate(contestants, ranks=rankings)

    for updated_score in updated_scores:
      cID = updated_score.keys()[0]
      new_mu = updated_score[cID].mu
      new_sigma = updated_score[cID].sigma
      isTie = len(set(rankings)) <= 1
      MongoInstance.updateScore(pID, cID, mID, new_mu, new_sigma, isTie)

    vID = str(vote['_id'])
    MongoInstance.setVoteFlagged(pID, vID)

  # print 'Done processing votes!'


# calculate percentiles, and solve for ranks
def calculatePercentilesAndRanks(MongoInstance, pID):
  mIDs = getmIDs(MongoInstance,pID)
  scoresBymID = dict([(mID, []) for mID in mIDs])
  votesBymID = dict([(mID, []) for mID in mIDs])
  tiesRatioBymID = dict([(mID, []) for mID in mIDs])

  allScoreDocs = MongoInstance.client[pID]['scores'].find()

  # For each metric of each score doc, fill the respective object with the associated value
  for scoreDoc in allScoreDocs:
    for mID in scoreDoc['scores']:
      scoresBymID[mID].append(scoreDoc['scores'][mID])
      votesBymID[mID].append(scoreDoc['num_votes'][mID])
      if scoreDoc['num_votes'][mID] == 0:
        tieRatio = 0
      else:
        tieRatio = (scoreDoc['num_ties'][mID]/float(scoreDoc['num_votes'][mID]))
      tiesRatioBymID[mID].append(tieRatio)

  votesPercentiles = {}
  tiesPercentiles = {}

  # Sort all scores
  # Calculate and store percentiles, indexed by the num_votes or num_ties
  for mID in scoresBymID:
    scoresBymID[mID].sort(reverse=True)
    thisVotesSeries = pd.Series(data=votesBymID[mID])
    thisTiesSeries = pd.Series(data=tiesRatioBymID[mID])

    thisVotesCounts = thisVotesSeries.value_counts()
    thisTiesCounts = thisTiesSeries.value_counts()    

    votesPercentiles[mID] = thisVotesCounts.sort_index().cumsum()*1./len(thisVotesSeries)
    tiesPercentiles[mID] = thisTiesCounts.sort_index().cumsum()*1./len(thisTiesSeries)


  usedRanks = dict([(mID, set()) for mID in mIDs]) # Keep track of which ranks have been used to avoid duplicate ranks
  incrementBy = 0 # variable to help us properly assign ranks when duplicates exist

  new_vote_percentiles = {}
  new_tie_percentiles = {}
  new_votability = {}

  
  # Now that we have all the scores and ranks calculated, iterate through each 
  # score doc again and match the right cID to each of the calculated values.
  # Built those into objects and then send them over to be added to the db
  allScoreDocs = MongoInstance.client[pID]['scores'].find()
  for scoreDoc in allScoreDocs:
    new_ranks = {}
    for mID in scoreDoc['scores']:
      foundValidIndex = False
      thisScore = scoreDoc['scores'][mID]
      while not foundValidIndex:
        tempIndex = scoresBymID[mID].index(thisScore)+incrementBy
        if tempIndex not in usedRanks[mID]:
          foundValidIndex = True
          incrementBy = 0
          usedRanks[mID].add(tempIndex)
          new_ranks[mID] = tempIndex
        else:
          incrementBy += 1

      new_vote_percentiles[mID] = votesPercentiles[mID][scoreDoc['num_votes'][mID]]
      if scoreDoc['num_votes'][mID] == 0:
        tieRatio = 0
      else:
        tieRatio = (scoreDoc['num_ties'][mID]/float(scoreDoc['num_votes'][mID]))
      new_tie_percentiles[mID] = tiesPercentiles[mID][tieRatio]
        
    for mID in scoreDoc['scores']:
      # print scoreDoc['num_votes'][mID]
      # print '-----'
      # print new_vote_percentiles[mID]
      # print new_tie_percentiles[mID]
      new_votability[mID] = [(1-new_vote_percentiles[mID])*(1-new_tie_percentiles[mID]),0]
      # new_votability[mID] = 1.0-(new_vote_percentiles[mID]/2.0)-(new_tie_percentiles[mID]/2.0)

    cID = scoreDoc['cID']
    MongoInstance.updatePercentilesAndRanks(pID,cID,new_vote_percentiles,new_tie_percentiles,new_ranks, new_votability)




# # When this gets run as a cron job - iterate through each project and run the analysis for each
# listOfProjects = [project['pID'] for project in MongoInstance.client['quantify']['projects'].find()]
# for pID in listOfProjects:
#   processVotes(pID)
#   calculatePercentilesAndRanks(pID)



