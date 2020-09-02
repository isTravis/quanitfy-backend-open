#!/usr/bin/python
'''
QUANTIFY Restful API Unit Tests
'''
from quantify import PORT
from db import MongoInstance

import nose
from nose.tools import eq_, ok_, with_setup
import json
import requests as r
from run_analysis import processVotes, calculatePercentilesAndRanks

# TODO:
# Mock valid and invalid key, project name, admin
# Global ensured clean-up
# Test Key

INCOMP_URL = 'http://localhost:%s/api/' % PORT
URL = INCOMP_URL + '%s'

key = 'test'

############################
# Project Tests
############################

def setup_project():
  MongoInstance.postThing('', 'project', project_title='test_project', owner_email='test@test.com', owner_first_name='Alex', owner_last_name='Is Rich')

def teardown_project():
  MongoInstance.deleteThing('test_project', 'projects', [])

@with_setup(teardown_project)
def test_post_single_project():
  # TODO: Post multiple projects
  params = {
      'projectTitle': 'test_project',
      'ownerEmail': 'test@test.com',
      'ownerFirstName': 'Alex',
      'ownerLastName': 'Is Rich',
      'key': 'key'
  }
  result = json.loads(r.post(URL % 'project', params=params).content)
  eq_(result[0]['pID'], params['projectTitle'])

@with_setup(setup_project, teardown_project)
def test_post_repeat_project():
  params = {
      'projectTitle': 'test_project',
      'ownerEmail': 'test@test.com',
      'ownerFirstName': 'Alex',
      'ownerLastName': 'Is Rich',
      'key': 'key'
  }
  result = json.loads(r.post(URL % 'project', params=params).content)
  eq_(result[0][0], 'Please choose a unique project title')

@with_setup(setup_project, teardown_project)
def test_put_project():
  params = {
      'pID': 'test_project',
      'projectTitle': 'test_project',
      'ownerEmail': 'test@test.com',
      'ownerFirstName': 'Alex',
      'ownerLastName': 'Is Rich',
      'key': 'key'
  }
  result = json.loads(r.put(URL % 'project', params=params).content)
  ok_(result[0]['updatedExisting'])

@with_setup(setup_project, teardown_project)
def test_get_existing_project():
  params = {
      'pID': 'test_project',
      'key': 'key'
  }
  result = json.loads(r.get(URL % 'project', params=params).content)
  eq_(result[0]['pID'], params['pID'])

@with_setup(setup_project, teardown_project)
def test_delete_existing_project():
  params = {
      'pID': 'test_project',
      'key': 'key'
  }
  result = json.loads(r.delete(URL % 'project', params=params).content)
  ok_(result[0]['deleted'])


############################
# Metric Tests
############################

class test_Metric(object):
    
    def setup(self):
        MongoInstance.postThing('', 'project', project_title='test_project', owner_email='test@test.com', owner_first_name='Alex', owner_last_name='Is Rich')
        self.mID1 = MongoInstance.postThing('test_project','metric',metric_name='contentment', metric_prefix='What is ')
        self.mID2 = MongoInstance.postThing('test_project','metric',metric_name='happiness', metric_prefix='How is ')     
 
    def teardown(self):
        MongoInstance.deleteThing('test_project', 'projects', [])


    def test_get_metric(self):
        params = {
            'pID': 'test_project',
            'mID': [self.mID1],
            'key': 'key'
        }
        result = json.loads(r.get(URL % 'metric', params=params).content)
        eq_(result[0]['mID'], params['mID'][0])

    def test_get_multiple_metrics(self):
        params = {
            'pID': 'test_project',
            'mID': [self.mID1,self.mID2],
            'key': 'key'
        }
        result = json.loads(r.get(URL % 'metric', params=params).content)
        resultIDs = []
        for item in result:
            resultIDs.append(item['mID'])
        eq_(resultIDs.sort(), params['mID'].sort())
        
    def test_post_metric(self):
        params = [
          ('name', 'contentment'),
          ('prefix', 'Which better expresses'),
          ('pID', 'test_project'),
          ('key', 'key')
        ]
        mIDs = json.loads(r.post(URL % 'metric', params=params).content)
        
        getResult = MongoInstance.getThing('test_project','metrics',mIDs)
        eq_(getResult[0]['metric'], 'contentment')

    def test_post_multiple_metrics(self):
        params = [
          ('name', 'contentment'),
          ('prefix', 'Which better expresses'),
          ('name', 'anger'),
          ('prefix', 'Which better represents'),
          ('pID', 'test_project'),
          ('key', 'key')
        ]
        mIDs = json.loads(r.post(URL % 'metric', params=params).content)
        
        getResult = MongoInstance.getThing('test_project','metrics',mIDs)
        eq_([getResult[0]['metric'],getResult[1]['metric']], ['contentment','anger'])

    ## TODO - Implement the proper error return when we detect a duplicate entry in db.py or quantify.py
    #
    # def test_post_duplicate_metric(self):
    #     params = [
    #       ('name', 'anger'),
    #       ('prefix', 'Which better expresses'),
    #       ('name', 'anger'),
    #       ('prefix', 'Which better expresses'),
    #       ('pID', 'test_project'),
    #       ('key', 'key')
    #     ]
    #     mIDs = json.loads(r.post(URL % 'metric', params=params).content)
        
    #     getResult = MongoInstance.getThing('test_project','metrics',mIDs)
    #     print getResult
    
    def test_delete_metric(self):
        params = [
          ('mID', self.mID1),
          # ('mID', self.mID2),
          ('pID', 'test_project'),
          ('key', 'key')
        ]
        mIDs = json.loads(r.delete(URL % 'metric', params=params).content)
        getMetricTry = MongoInstance.getThing('test_project','metrics',[self.mID1])
        eq_(getMetricTry, [])

    def test_delete_multiple_metrics(self):
        params = [
          ('mID', self.mID1),
          ('mID', self.mID2),
          ('pID', 'test_project'),
          ('key', 'key')
        ]
        mIDs = json.loads(r.delete(URL % 'metric', params=params).content)
        getMetricsTry = MongoInstance.getThing('test_project','metrics',[self.mID1,self.mID2])
        eq_(getMetricsTry, [])



############################
# Content Tests
############################

class test_Content(object):
    
    def setup(self):
        MongoInstance.postThing('', 'project', project_title='test_project', owner_email='test@test.com', owner_first_name='Alex', owner_last_name='Is Rich')
        self.cID1 = MongoInstance.postThing('test_project','content',content="should Store this Text", content_type="text", content_data={'color': 'black', 'size': 'fonty'})
        self.cID2 = MongoInstance.postThing('test_project','content',content="http://www.pixeljoint.com/files/icons/full/cat__r177950541.gif", content_type="jpg", content_data={'color':"red", 'size':"big"})

    def teardown(self):
        MongoInstance.deleteThing('test_project', 'projects', [])


    def test_get_content(self):
        params = {
            'pID': 'test_project',
            'cID': [self.cID1],
            'key': 'key'
        }
        result = json.loads(r.get(URL % 'content', params=params).content)
        eq_(result[0]['cID'], params['cID'][0])

    def test_get_multiple_contents(self):
        params = {
            'pID': 'test_project',
            'cID': [self.cID1,self.cID2],
            'key': 'key'
        }
        result = json.loads(r.get(URL % 'content', params=params).content)
        resultIDs = []
        for item in result:
            resultIDs.append(item['cID'])
        eq_(resultIDs.sort(), params['cID'].sort())
        
    def test_post_content(self):
        params = [
          ('content', 'puddle-puppy'),
          ('content_type', 'text'),
          ('content_data', '{isRabbit:False}'),
          ('pID', 'test_project'),
          ('key', 'key')
        ]
        cIDs = json.loads(r.post(URL % 'content', params=params).content)

        getResult = MongoInstance.getThing('test_project','content',cIDs)
        eq_(getResult[0]['content'], 'puddle-puppy')


    def test_post_multiple_contents(self):
        params = [
          ('content', 'puddle-puppy'),
          ('content_type', 'text'),
          ('content_data', '{isRabbit:False}'),
          ('content', 'http://s.huffpost.com/contributors/kevin-k-murphy/headshot.jpg'),
          ('content_type', 'jpg'),
          ('content_data', '{isRabbit:True}'),
          ('pID', 'test_project'),
          ('key', 'key')
        ]

        cIDs = json.loads(r.post(URL % 'content', params=params).content)
        getResult = MongoInstance.getThing('test_project','content',cIDs)
        eq_([getResult[0]['content'],getResult[1]['content']], ['puddle-puppy','http://s.huffpost.com/contributors/kevin-k-murphy/headshot.jpg'])

    # ## TODO - Implement the proper error return when we detect a duplicate entry in db.py or quantify.py
    # #
    # # def test_post_duplicate_metric(self):
    # #     params = [
    # #       ('name', 'anger'),
    # #       ('prefix', 'Which better expresses'),
    # #       ('name', 'anger'),
    # #       ('prefix', 'Which better expresses'),
    # #       ('pID', 'test_project'),
    # #       ('key', 'key')
    # #     ]
    # #     mIDs = json.loads(r.post(URL % 'metric', params=params).content)
        
    # #     getResult = MongoInstance.getThing('test_project','metrics',mIDs)
    # #     print getResult
    
    def test_delete_content(self):
        params = [
          ('cID', self.cID1),
          ('pID', 'test_project'),
          ('key', 'key')
        ]
        cIDs = json.loads(r.delete(URL % 'content', params=params).content)
        getMetricTry = MongoInstance.getThing('test_project','content',[self.cID1])
        eq_(getMetricTry, [])

    def test_delete_multiple_contents(self):
        params = [
          ('cID', self.cID1),
          ('cID', self.cID2),
          ('pID', 'test_project'),
          ('key', 'key')
        ]
        cIDs = json.loads(r.delete(URL % 'content', params=params).content)
        getMetricsTry = MongoInstance.getThing('test_project','content',[self.cID1,self.cID2])
        eq_(getMetricsTry, [])


############################
# User Tests
############################

class test_User(object):
    
    def setup(self):
        MongoInstance.postThing('', 'project', project_title='test_project', owner_email='test@test.com', owner_first_name='Alex', owner_last_name='Is Rich')
        self.uID1 = MongoInstance.postThing('test_project','user',user_data="TravIsRich")
        self.uID2 = MongoInstance.postThing('test_project','user',user_data="AlexIsHope")

    def teardown(self):
        MongoInstance.deleteThing('test_project', 'projects', [])


    def test_get_user(self):
        params = {
            'pID': 'test_project',
            'uID': [self.uID1],
            'key': 'key'
        }
        result = json.loads(r.get(URL % 'user', params=params).content)
        eq_(result[0]['uID'], params['uID'][0])

    def test_get_multiple_users(self):
        params = {
            'pID': 'test_project',
            'uID': [self.uID1,self.uID2],
            'key': 'key'
        }
        result = json.loads(r.get(URL % 'user', params=params).content)
        resultIDs = []
        for item in result:
            resultIDs.append(item['uID'])
        eq_(resultIDs.sort(), params['uID'].sort())
        
    def test_post_user(self):
        params = [
          ('user_data', 'KevIsHu'),
          # ('user_data', 'DeepIsPak'),
          ('pID', 'test_project'),
          ('key', 'key')
        ]
        uIDs = json.loads(r.post(URL % 'user', params=params).content)
        getResult = MongoInstance.getThing('test_project','users',uIDs)
        eq_(getResult[0]['user_data'], 'KevIsHu')


    def test_post_multiple_contents(self):
        params = [
          ('user_data', 'KevIsHu'),
          ('user_data', 'DeepIsPak'),
          ('pID', 'test_project'),
          ('key', 'key')
        ]

        uIDs = json.loads(r.post(URL % 'user', params=params).content)
        getResult = MongoInstance.getThing('test_project','users',uIDs)
        eq_([getResult[0]['user_data'],getResult[1]['user_data']], ['KevIsHu','DeepIsPak'])

    # ## TODO - Implement the proper error return when we detect a duplicate entry in db.py or quantify.py
    # #
    # # def test_post_duplicate_metric(self):
    # #     params = [
    # #       ('name', 'anger'),
    # #       ('prefix', 'Which better expresses'),
    # #       ('name', 'anger'),
    # #       ('prefix', 'Which better expresses'),
    # #       ('pID', 'test_project'),
    # #       ('key', 'key')
    # #     ]
    # #     mIDs = json.loads(r.post(URL % 'metric', params=params).content)
        
    # #     getResult = MongoInstance.getThing('test_project','metrics',mIDs)
    # #     print getResult
    
    def test_delete_content(self):
        params = [
          ('uID', self.uID1),
          ('pID', 'test_project'),
          ('key', 'key')
        ]
        uIDs = json.loads(r.delete(URL % 'user', params=params).content)
        getMetricTry = MongoInstance.getThing('test_project','users',[self.uID1])
        eq_(getMetricTry, [])

    def test_delete_multiple_contents(self):
        params = [
          ('uID', self.uID1),
          ('uID', self.uID2),
          ('pID', 'test_project'),
          ('key', 'key')
        ]
        uIDs = json.loads(r.delete(URL % 'user', params=params).content)
        getMetricsTry = MongoInstance.getThing('test_project','users',[self.uID1,self.uID2])
        eq_(getMetricsTry, [])



############################
# Vote Tests
############################
class test_Vote(object):
    
    def setup(self):
        MongoInstance.postThing('', 'project', project_title='test_project', owner_email='test@test.com', owner_first_name='Alex', owner_last_name='Is Rich')
        self.mID  = MongoInstance.postThing('test_project','metric',metric_name='contentment', metric_prefix='What is ')
        self.cID1 = MongoInstance.postThing('test_project','content',content="should Store this Text", content_type="text", content_data={'color': 'black', 'size': 'fonty'})
        self.cID2 = MongoInstance.postThing('test_project','content',content="http://www.pixeljoint.com/files/icons/full/cat__r177950541.gif", content_type="jpg", content_data={'color':"red", 'size':"big"})
        self.uID  = MongoInstance.postThing('test_project','user',user_data="TravIsRich")
        self.vID1 = MongoInstance.postThing('test_project', 'vote', mID=self.mID, vote_result={self.cID1:1,self.cID2:2}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
        self.vID2 = MongoInstance.postThing('test_project', 'vote', mID=self.mID, vote_result={self.cID2:1,self.cID1:2}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})

    def teardown(self):
        MongoInstance.deleteThing('test_project', 'projects', [])


    def test_get_vote(self):
        params = {
            'pID': 'test_project',
            'vID': [self.vID1],
            'key': 'key'
        }
        result = json.loads(r.get(URL % 'vote', params=params).content)
        eq_(result[0]['vID'], params['vID'][0])

    def test_get_multiple_votes(self):
        params = {
            'pID': 'test_project',
            'vID': [self.vID1,self.vID2],
            'key': 'key'
        }
        result = json.loads(r.get(URL % 'vote', params=params).content)
        resultIDs = []
        for item in result:
            resultIDs.append(item['vID'])
        eq_(resultIDs.sort(), params['vID'].sort())
        
    def test_post_vote(self):
        params = [
          ('vote_result', {self.cID1:1,self.cID2:2}),
          ('vote_data', {'cat':'aSuperCoolCat'}),
          ('mID', self.mID),
          ('uID', self.uID),
          ('voter_ip', '192.168.1.68'),
          ('pID', 'test_project'),
          ('key', 'key')
        ]

        vIDs = json.loads(r.post(URL % 'vote', params=params).content)
        getResult = MongoInstance.getThing('test_project','votes',vIDs)
        eq_(getResult[0]['voter_ip'], '192.168.1.68')


    def test_post_multiple_votes(self):
        params = [
          ('vote_result', {self.cID1:1,self.cID2:2}),
          ('vote_data', {'cat':'aSuperCoolCat'}),
          ('vote_result', {self.cID1:3,self.cID2:5}),
          ('vote_data', {'dog':'aDumbDog'}),
          ('mID', self.mID),
          ('uID', self.uID),
          ('voter_ip', '192.168.1.68'),
          ('pID', 'test_project'),
          ('key', 'key')
        ]

        vIDs = json.loads(r.post(URL % 'vote', params=params).content)
        getResult = MongoInstance.getThing('test_project','votes',vIDs)
        eq_([getResult[0]['vote_data'],getResult[1]['vote_data']], ['cat', 'dog'])

    ## TODO - Implement the proper error return when we detect a duplicate entry in db.py or quantify.py
    #
    # def test_post_duplicate_metric(self):
    #     params = [
    #       ('name', 'anger'),
    #       ('prefix', 'Which better expresses'),
    #       ('name', 'anger'),
    #       ('prefix', 'Which better expresses'),
    #       ('pID', 'test_project'),
    #       ('key', 'key')
    #     ]
    #     mIDs = json.loads(r.post(URL % 'metric', params=params).content)
    #     getResult = MongoInstance.getThing('test_project','metrics',mIDs)
    #     print getResult
    

############################
# Achievements Tests
############################
class test_Achievements(object):
    
    def setup(self):
        MongoInstance.postThing('', 'project', project_title='test_project', owner_email='test@test.com', owner_first_name='Alex', owner_last_name='Is Rich')
        self.aID1 = MongoInstance.postThing('test_project','achievement', achievement_data={'aThing':5})
        self.aID2 = MongoInstance.postThing('test_project','achievement', achievement_data={'bThing':7})

    def teardown(self):
        MongoInstance.deleteThing('test_project', 'projects', [])


    def test_get_achievement(self):
        params = {
            'pID': 'test_project',
            'aID': [self.aID1],
            'key': 'key'
        }
        result = json.loads(r.get(URL % 'achievement', params=params).content)
        eq_(result[0]['aID'], params['aID'][0])

    def test_get_multiple_achievements(self):
        params = {
            'pID': 'test_project',
            'aID': [self.aID1,self.aID2],
            'key': 'key'
        }
        result = json.loads(r.get(URL % 'achievement', params=params).content)
        resultIDs = []
        for item in result:
            resultIDs.append(item['aID'])
        eq_(resultIDs.sort(), params['aID'].sort())
        
    def test_post_achievement(self):
        params = [
          ('achievement_data', {'aThing':5}),
          ('pID', 'test_project'),
          ('key', 'key')
        ]
        aIDs = json.loads(r.post(URL % 'achievement', params=params).content)
        getResult = MongoInstance.getThing('test_project','achievements',aIDs)
        eq_(getResult[0]['achievement_data'], 'aThing')


    def test_post_multiple_achievements(self):
        params = [
          ('achievement_data', {'aThing':5}),
          ('achievement_data', {'bThing':7}),
          ('pID', 'test_project'),
          ('key', 'key')
        ]

        aIDs = json.loads(r.post(URL % 'achievement', params=params).content)
        getResult = MongoInstance.getThing('test_project','achievements',aIDs)
        eq_([getResult[0]['achievement_data'],getResult[1]['achievement_data']], ['aThing','bThing'])

    ## TODO - Implement the proper error return when we detect a duplicate entry in db.py or quantify.py
    #
    # def test_post_duplicate_metric(self):
    #     params = [
    #       ('name', 'anger'),
    #       ('prefix', 'Which better expresses'),
    #       ('name', 'anger'),
    #       ('prefix', 'Which better expresses'),
    #       ('pID', 'test_project'),
    #       ('key', 'key')
    #     ]
    #     mIDs = json.loads(r.post(URL % 'metric', params=params).content)
        
    #     getResult = MongoInstance.getThing('test_project','metrics',mIDs)
    #     print getResult
    
    def test_delete_achievement(self):
        params = [
          ('aID', self.aID1),
          ('pID', 'test_project'),
          ('key', 'key')
        ]
        aIDs = json.loads(r.delete(URL % 'achievement', params=params).content)
        getMetricTry = MongoInstance.getThing('test_project','achievements',[self.aID1])
        eq_(getMetricTry, [])

    def test_delete_multiple_achievements(self):
        params = [
          ('aID', self.aID1),
          ('aID', self.aID2),
          ('pID', 'test_project'),
          ('key', 'key')
        ]
        aIDs = json.loads(r.delete(URL % 'achievement', params=params).content)
        getMetricsTry = MongoInstance.getThing('test_project','achievements',[self.aID1,self.aID2])
        eq_(getMetricsTry, [])


############################
# Keys Tests
############################
class test_Keys(object):
    
    def setup(self):
        MongoInstance.postThing('', 'project', project_title='test_project', owner_email='test@test.com', owner_first_name='Alex', owner_last_name='Is Rich')
        self.kID1 = MongoInstance.postThing('test_project', 'key', is_admin=True)
        self.kID2 = MongoInstance.postThing('test_project', 'key', is_admin=False)

    def teardown(self):
        MongoInstance.deleteThing('test_project', 'projects', [])


    def test_get_key(self):
        params = {
            'pID': 'test_project',
            'kID': [self.kID1],
            'key': 'key'
        }
        result = json.loads(r.get(URL % 'key', params=params).content)
        eq_(result[0]['kID'], params['kID'][0])

    def test_get_multiple_keys(self):
        params = {
            'pID': 'test_project',
            'kID': [self.kID1,self.kID2],
            'key': 'key'
        }
        result = json.loads(r.get(URL % 'key', params=params).content)
        resultIDs = []
        for item in result:
            resultIDs.append(item['kID'])
        eq_(resultIDs.sort(), params['kID'].sort())
        
    def test_post_key(self):
        params = [
          ('is_admin', True),
          ('pID', 'test_project'),
          ('key', 'key')
        ]
        kIDs = json.loads(r.post(URL % 'key', params=params).content)
        getResult = MongoInstance.getThing('test_project','keys',kIDs)
        eq_(getResult[0]['admin'], 'True')


    def test_post_multiple_keys(self):
        params = [
          ('is_admin', True),
          ('is_admin', False),
          ('pID', 'test_project'),
          ('key', 'key')
        ]

        kIDs = json.loads(r.post(URL % 'key', params=params).content)
        getResult = MongoInstance.getThing('test_project','keys',kIDs)
        eq_([getResult[0]['admin'],getResult[1]['admin']], ['True','False'])

    ## TODO - Implement the proper error return when we detect a duplicate entry in db.py or quantify.py
    #
    # def test_post_duplicate_metric(self):
    #     params = [
    #       ('name', 'anger'),
    #       ('prefix', 'Which better expresses'),
    #       ('name', 'anger'),
    #       ('prefix', 'Which better expresses'),
    #       ('pID', 'test_project'),
    #       ('key', 'key')
    #     ]
    #     mIDs = json.loads(r.post(URL % 'metric', params=params).content)
        
    #     getResult = MongoInstance.getThing('test_project','metrics',mIDs)
    #     print getResult
    
    def test_delete_key(self):
        params = [
          ('kID', self.kID1),
          ('pID', 'test_project'),
          ('key', 'key')
        ]
        kIDs = json.loads(r.delete(URL % 'key', params=params).content)
        # print kIDs
        # print MongoInstance.deleteThing('test_project','keys',[self.kID1])
        getMetricTry = MongoInstance.getThing('test_project','keys',[self.kID1])
        eq_(getMetricTry, [])

    def test_delete_multiple_keys(self):
        params = [
          ('kID', self.kID1),
          ('kID', self.kID2),
          ('pID', 'test_project'),
          ('key', 'key')
        ]
        kIDs = json.loads(r.delete(URL % 'key', params=params).content)
        getMetricsTry = MongoInstance.getThing('test_project','keys',[self.kID1,self.kID2])
        eq_(getMetricsTry, [])







############################
# Contestants Tests
############################
class test_Contestants(object):
    
    def setup(self):
        MongoInstance.deleteThing('test_project', 'projects', [])
        MongoInstance.postThing('', 'project', project_title='test_project', owner_email='test@test.com', owner_first_name='Alex', owner_last_name='Is Rich')
        self.mID1  = MongoInstance.postThing('test_project','metric',metric_name='contentment', metric_prefix='What is ')
        self.mID2  = MongoInstance.postThing('test_project','metric',metric_name='garbage', metric_prefix='What is ')
        self.cID1 = MongoInstance.postThing('test_project','content',content="should Store this Text", content_type="text", content_data={'color': '1black', 'size': 'fonty'})
        self.cID2 = MongoInstance.postThing('test_project','content',content="http://www.pixeljoint.com/files/icons/full/cat__r177950541.gif", content_type="jpg", content_data={'color':"2black", 'size':"big"})
        self.cID3 = MongoInstance.postThing('test_project','content',content="should Store 3 Text", content_type="text", content_data={'color': '3black', 'size': '3fonty'})
        self.cID4 = MongoInstance.postThing('test_project','content',content="should Store 4 Text", content_type="text", content_data={'color': '4black', 'size': '4fonty'})
        self.cID5 = MongoInstance.postThing('test_project','content',content="should Store 5 Text", content_type="text", content_data={'color': '5black', 'size': '5fonty'})
        self.uID  = MongoInstance.postThing('test_project','user',user_data="TravIsRich")
        self.vID1 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID3:0,self.cID4:1}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
        self.vID2 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID4:0,self.cID5:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
        self.vID3 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID5:0,self.cID1:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
        self.vID4 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID1:0,self.cID2:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
        self.vID5 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID4:0,self.cID5:1}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
        self.vID6 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID5:1,self.cID3:0}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
        self.vID7 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID5:0,self.cID1:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
        self.vID8 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID2:0,self.cID1:0}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
        self.vID9 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID2:0,self.cID3:0}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
        self.vID10 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID1:0,self.cID2:0}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
        self.vIDa1 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID3:0,self.cID4:0}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
        self.vIDa2 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID2:0,self.cID5:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
        self.vIDa3 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID2:0,self.cID1:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
        self.vIDa4 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID1:0,self.cID2:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
        self.vIDa5 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID2:0,self.cID5:1}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
        self.vIDa6 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID2:1,self.cID3:0}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
        self.vIDa9 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID1:0,self.cID3:0}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
        self.vIDa10 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID1:0,self.cID2:0}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})

        # Voting on mID1 has been done such that rankings are [cID3,cID4,cID5,cID1,cID2]
        # print ' '
        processVotes('test_project')
        calculatePercentilesAndRanks('test_project')
    
    def teardown(self):
        MongoInstance.deleteThing('test_project', 'projects', [])


    def test_get_random_contestants(self):
        params = {
            'pID': 'test_project',
            'num_desired_contestants': 2,
            'mID': self.mID1,
            'mode': 'random',
            'key': 'key'
        }
        result = json.loads(r.get(URL % 'contestants', params=params).content)
        # eq_(result[0]['vID'], params['vID'][0])

    def test_get_weighted_contestants(self):
        params = {
            'pID': 'test_project',
            'num_desired_contestants': 3,
            'mID': self.mID1,
            'mode': 'weighted',
            'key': 'key'
        }

        result = json.loads(r.get(URL % 'contestants', params=params).content)
        # for thing in result:
        #   print thing['index']
        # eq_(result[0]['vID'], params['vID'][0])

############################
# Scores Tests
############################
class test_Scores(object):
  def setup(self):
        MongoInstance.postThing('', 'project', project_title='test_project', owner_email='test@test.com', owner_first_name='Alex', owner_last_name='Is Rich')
        self.mID1  = MongoInstance.postThing('test_project','metric',metric_name='contentment', metric_prefix='What is ')
        self.mID2  = MongoInstance.postThing('test_project','metric',metric_name='garbage', metric_prefix='What is ')
        self.cID1 = MongoInstance.postThing('test_project','content',content="should Store this Text", content_type="text", content_data={'color': '1black', 'size': 'fonty'})
        self.cID2 = MongoInstance.postThing('test_project','content',content="http://www.pixeljoint.com/files/icons/full/cat__r177950541.gif", content_type="jpg", content_data={'color':"2black", 'size':"big"})
        self.cID3 = MongoInstance.postThing('test_project','content',content="should Store 3 Text", content_type="text", content_data={'color': '3black', 'size': '3fonty'})
        self.cID4 = MongoInstance.postThing('test_project','content',content="should Store 4 Text", content_type="text", content_data={'color': '4black', 'size': '4fonty'})
        self.cID5 = MongoInstance.postThing('test_project','content',content="should Store 5 Text", content_type="text", content_data={'color': '5black', 'size': '5fonty'})
        self.uID  = MongoInstance.postThing('test_project','user',user_data="TravIsRich")
        self.vID1 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID3:0,self.cID4:1}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
        self.vID2 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID4:0,self.cID5:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
        self.vID3 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID5:0,self.cID1:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
        self.vID4 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID1:0,self.cID2:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
        self.vID5 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID4:0,self.cID5:1}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
        self.vID6 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID5:1,self.cID3:0}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
        self.vID7 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID5:0,self.cID1:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
        self.vID8 = MongoInstance.postThing('test_project', 'vote', mID=self.mID2, vote_result={self.cID2:0,self.cID1:0}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
        self.vID9 = MongoInstance.postThing('test_project', 'vote', mID=self.mID2, vote_result={self.cID2:0,self.cID3:0}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
        self.vID10 = MongoInstance.postThing('test_project', 'vote', mID=self.mID2, vote_result={self.cID1:0,self.cID2:0}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
        # Voting on mID1 has been done such that rankings are [cID3,cID4,cID5,cID1,cID2]

  def teardown(self):
      MongoInstance.deleteThing('test_project', 'projects', [])


  def test_get_scores(self):
    processVotes('test_project')
    calculatePercentilesAndRanks('test_project')
    # print MongoInstance.getScores('test_project',[self.cID3])
    # print MongoInstance.getScores('test_project',[self.cID4])
    # print MongoInstance.getScores('test_project',[self.cID5])
    # print MongoInstance.getScores('test_project',[self.cID1])
    # print MongoInstance.getScores('test_project',[self.cID2])
    # eq_(result[0]['vID'], params['vID'][0])
    params = {
        'pID': 'test_project',
        'cID': [self.cID1, self.cID2],
        'key': 'key'
    }

    result = json.loads(r.get(URL % 'scores', params=params).content)
    scores = MongoInstance.client['test_project'].scores.find({ 'cID': { '$in': [self.cID5]}})
    # scoreVectors = [{'cID': item['cID'], 'scoreVector': item['scores']} for item in scores]
    # for score in scores:
    #   print score['votability']
    #   print score['vote_percentiles']
    #   print score['tie_percentiles']

############################
# Results Tests
############################
class test_Results(object):
  def setup(self):
    MongoInstance.postThing('', 'project', project_title='test_project', owner_email='test@test.com', owner_first_name='Alex', owner_last_name='Is Rich')
    self.mID1  = MongoInstance.postThing('test_project','metric',metric_name='contentment', metric_prefix='What is ')
    self.mID2  = MongoInstance.postThing('test_project','metric',metric_name='garbage', metric_prefix='What is ')
    self.cID1 = MongoInstance.postThing('test_project','content',content="should Store this Text", content_type="text", content_data={'color': '1black', 'size': 'fonty'})
    self.cID2 = MongoInstance.postThing('test_project','content',content="http://www.pixeljoint.com/files/icons/full/cat__r177950541.gif", content_type="jpg", content_data={'color':"2black", 'size':"big"})
    self.cID3 = MongoInstance.postThing('test_project','content',content="should Store 3 Text", content_type="text", content_data={'color': '3black', 'size': '3fonty'})
    self.cID4 = MongoInstance.postThing('test_project','content',content="should Store 4 Text", content_type="text", content_data={'color': '4black', 'size': '4fonty'})
    self.cID5 = MongoInstance.postThing('test_project','content',content="should Store 5 Text", content_type="text", content_data={'color': '5black', 'size': '5fonty'})
    self.uID  = MongoInstance.postThing('test_project','user',user_data="TravIsRich")
    self.vID1 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID3:0,self.cID4:1}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
    self.vID2 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID4:0,self.cID5:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
    self.vID3 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID5:0,self.cID1:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
    self.vID4 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID1:0,self.cID2:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
    self.vID5 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID4:0,self.cID5:1}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
    self.vID6 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID5:1,self.cID3:0}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
    self.vID7 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID5:0,self.cID1:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
    self.vID8 = MongoInstance.postThing('test_project', 'vote', mID=self.mID2, vote_result={self.cID2:0,self.cID1:0}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
    self.vID9 = MongoInstance.postThing('test_project', 'vote', mID=self.mID2, vote_result={self.cID2:0,self.cID3:0}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
    self.vID10 = MongoInstance.postThing('test_project', 'vote', mID=self.mID2, vote_result={self.cID1:0,self.cID2:0}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
    # Voting on mID1 has been done such that rankings are [cID3,cID4,cID5,cID1,cID2]
    processVotes('test_project')
    calculatePercentilesAndRanks('test_project')

  def teardown(self):
    MongoInstance.deleteThing('test_project', 'projects', [])


  def test_get_results(self):
    # for x in MongoInstance.getResults('test_project',self.mID1,1,1,5):
    #   print x
    params = {
        'pID': 'test_project',
        'mID': self.mID1,
        'sort': 1,
        'skip': 1,
        'limit': 5,
        'key': 'key'
    }

    result = json.loads(r.get(URL % 'results', params=params).content)

    # for x in result:
    #   print x
      

############################
# Search Tests
############################
class test_Search(object):
  def setup(self):
    MongoInstance.postThing('', 'project', project_title='test_project', owner_email='test@test.com', owner_first_name='Alex', owner_last_name='Is Rich')
    self.mID1  = MongoInstance.postThing('test_project','metric',metric_name='contentment', metric_prefix='What is ')
    self.mID2  = MongoInstance.postThing('test_project','metric',metric_name='garbage', metric_prefix='What is ')
    self.cID1 = MongoInstance.postThing('test_project','content',content="should Store this Text", content_type="text", content_data={'color': '1black', 'size': 'fonty'})
    self.cID2 = MongoInstance.postThing('test_project','content',content="http://www.pixeljoint.com/files/icons/full/cat__r177950541.gif", content_type="jpg", content_data={'color':"2black", 'size':"big"})
    self.cID3 = MongoInstance.postThing('test_project','content',content="should Store 3 Text", content_type="text", content_data={'color': '3black', 'size': '3fonty'})
    self.cID4 = MongoInstance.postThing('test_project','content',content="should Store 4 Text", content_type="text", content_data={'color': '4black', 'size': '4fonty'})
    self.cID5 = MongoInstance.postThing('test_project','content',content="should Store 5 Text", content_type="text", content_data={'color': '5black', 'size': '5fonty'})
    self.uID  = MongoInstance.postThing('test_project','user',user_data="TravIsRich")
    self.vID1 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID3:0,self.cID4:1}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
    self.vID2 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID4:0,self.cID5:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
    self.vID3 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID5:0,self.cID1:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
    self.vID4 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID1:0,self.cID2:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
    self.vID5 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID4:0,self.cID5:1}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
    self.vID6 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID5:1,self.cID3:0}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
    self.vID7 = MongoInstance.postThing('test_project', 'vote', mID=self.mID1, vote_result={self.cID5:0,self.cID1:1}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
    self.vID8 = MongoInstance.postThing('test_project', 'vote', mID=self.mID2, vote_result={self.cID2:0,self.cID1:0}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
    self.vID9 = MongoInstance.postThing('test_project', 'vote', mID=self.mID2, vote_result={self.cID2:0,self.cID3:0}, voter_ip='192.168.1.23', uID=self.uID, vote_data={'cat':'aSuperLameCat'})
    self.vID10 = MongoInstance.postThing('test_project', 'vote', mID=self.mID2, vote_result={self.cID1:0,self.cID2:0}, voter_ip='192.168.1.68', uID=self.uID, vote_data={'cat':'aSuperCoolCat'})
    # Voting on mID1 has been done such that rankings are [cID3,cID4,cID5,cID1,cID2]
    processVotes('test_project')
    calculatePercentilesAndRanks('test_project')

  def teardown(self):
    MongoInstance.deleteThing('test_project', 'projects', [])


  def test_get_search(self):
    # for x in MongoInstance.getResults('test_project',self.mID1,1,1,5):
    #   print x
    params = {
        ('pID', 'test_project'),
        ('mID', self.mID1),
        ('metric_score', 1.0),
        ('mID', self.mID2),
        ('metric_score', 0.5),
        ('key', 'key')
    }
    result = json.loads(r.get(URL % 'search', params=params).content)
    # print ' ' 
    # for x in result:
    #   print "distance="+str(x['distance']), "cID="+str(x['cID']), "rank="+str(x['rank']), "data="+x['content_data']['color']


  def test_search_skip_and_limit(self):
    params = {
        ('pID', 'test_project'),
        ('mID', self.mID1),
        ('metric_score', 1.0),
        ('mID', self.mID2),
        ('metric_score', 0.5),
        ('skip', 1),
        ('limit', 3),
        ('key', 'key')
    }
    result = json.loads(r.get(URL % 'search', params=params).content)

    # print ' ' 
    # for x in result:
    #   print "distance="+str(x['distance']), "cID="+str(x['cID']), "rank="+str(x['rank']), "data="+x['content_data']['color']

















