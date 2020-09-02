import math
import pymongo
from pymongo import GEO2D
from bson.objectid import ObjectId
import os
import urllib
import random
import time
import json
from operator import itemgetter
import random
import sys
from clientrun_analysis import processVotes, calculatePercentilesAndRanks
from clientrun_analysis_user import processVotes as processVotesUser
from clientrun_analysis_user import calculatePercentilesAndRanks as calculatePercentilesAndRanksUser



# def generateKey(pID, is_admin):
#     isUnique = False;
#     while isUnique == False: # While we haven't found a unique ID
#         key = os.urandom(6).encode('hex') # Generate a 6-byte (12 letter, 0-10 a-f) publicKey
#         if MongoInstance.client[pID].keys.find_one({'key': key}) == None: # If the ID is unique, that is, no projects with that pID are returned
#             isUnique = True # set isUnique true, loop will end
#     return {'key':key, 'admin':is_admin}

def formatObjectIDs(collectionName, results):
    for result in results: # For each result is passed, convert the _id to the proper mID, cID, etc.
        result[collectionName[0]+'ID'] = str(result.pop('_id')) # Note the .pop removes the _id from the dict
    return results

def getmIDs(pID):
    mIDs = []
    metrics = MongoInstance.client[pID]['metrics'].find()
    for metric in metrics:
        mIDs.append(str(metric['_id']))
    return mIDs

class mongoInstance(object):
    ############################
    # Authentication
    ############################
    def isValidPublic(self,pID,key):
        try:
            return MongoInstance.client[pID].keys.find_one({'_id': ObjectId(key)}) != None
        except:
            return False
    def isValidAdmin(self,pID,key):
        try:
            return MongoInstance.client[pID].keys.find_one({'_id': ObjectId(key), 'admin':True}) != None
        except:
            return False

    # Check if the specified key for a given pID has admin priveleges
    # def isAdmin(self, pID, key):
    #     return MongoInstance.client[pID].keys.find_one({'_id': ObjectId(key)})['admin']


    ############################
    # Project
    ############################

    def getProject(self,pID):
        # if collectionName == 'projects':
        return MongoInstance.client['quantify']['projects'].find_one({'pID': pID}, {'_id': 0})

    def putProject(self, pID, **kwargs): # content_url="", metadata={}, metric_name='', metric_prefix='', user_data={}, vote_results={}, voter_ip='0.0.0.0', uID='', vote_data={}, mID='',key_type=''):
        updateFields = {}
        for arg in kwargs:
            if kwargs[arg] != None:
                updateFields[arg] = kwargs[arg]

        return MongoInstance.client['quantify'].projects.update({'pID':pID}, {"$set": updateFields}, upsert=False)

    def postProject(self, **kwargs):
        project_title = kwargs['project_title']
        owner_email = kwargs['owner_email']
        owner_first_name = kwargs['owner_first_name']
        owner_last_name = kwargs['owner_last_name']
        description = kwargs['description']

        # Format the project title to properly be a Mongo db name 
        # Must be less than 64 characters. No spaces
        pID = project_title.replace(" ", "_").lower()

        if pID in MongoInstance.client.database_names():
            return "Please choose a unique project title", 400
        else:
            # Add the project to the quantify DB 
            MongoInstance.client['quantify'].projects.insert({"pID": pID, "project_title": project_title, "owner_email": owner_email, "owner_first_name": owner_first_name, "owner_last_name": owner_last_name, "description": description, "date_created":int(time.time())}) 
            
            # Create DB for the project
            db = MongoInstance.client[pID]
            
            # Generate and add Admin and Public Key
            adminKey = str(db['keys'].insert({'admin':True}))
            publicKey = str(db['keys'].insert({'admin':False}))

            # Create keys Collection and insert the new ones
            # db['keys'].insert([adminKey,publicKey])

            return {'pID':pID, 'adminKey':adminKey, 'publicKey':publicKey }

    def deleteProject(self, pID):
        # Drop top-level DB
        MongoInstance.client.drop_database(pID)
        # Drop DB document in quantify databases collection
        MongoInstance.client['quantify']['projects'].remove({'pID': pID})             
        return {'deleted': True}


    ############################
    # User
    ############################
    # def getUser()
    # objectIDs = []
    #     for thingID in thingIDs:
    #         objectIDs.append(ObjectId(thingID))

    #     # if collectionName == 'projects':
    #     #     return MongoInstance.client['quantify'][collectionName].find_one({'pID': pID}, {'_id': 0})

    #     if collectionName == 'users':
    #         return formatObjectIDs(collectionName,[x for x in MongoInstance.client['quantify'][collectionName].find({'_id':{"$in":objectIDs}})])

    # ////
    # elif thingType == 'user':
    #         uID = kwargs['uID']
    #         updateFields = {}
    #         for arg in kwargs:
    #             if kwargs[arg] != None:
    #                 updateFields[arg] = kwargs[arg]

    #         return MongoInstance.client[pID].users.update({'uID':uID}, {"$set": updateFields}, upsert=False)

    def createUser(self, pID):
        results = []
        colors = ['Almond', 'Amber', 'Apricot', 'Aqua', 'Aquamarine', 'Ash', 'Asparagus', 'Beige', 'Black', 'Blue', 'Blush', 'Brass', 'Bronze', 'Brown', 'Cerulean', 'Charcoal', 'Chestnut', 'Copper', 'Cornflower', 'Cyan', 'Dandelion', 'Denim', 'Eggplant', 'Fern', 'Fuchsia', 'Gold', 'Goldenrod', 'Gray', 'Green', 'Indigo', 'Ivory', 'Khaki', 'Lavender', 'Lime', 'Magenta', 'Mahogany', 'Maroon', 'Melon', 'Navy', 'Olive', 'Orange', 'Orchid', 'Peach', 'Pink', 'Periwinkle', 'Platinum', 'Plum', 'Razzmatazz', 'Red', 'Salmon', 'Scarlet', 'Sepia', 'Shadow', 'Shamrock', 'Snow', 'Silver', 'Sunglow', 'Tan', 'Teal', 'Tumbleweed', 'Violet', 'Wheat', 'White', 'Yellow']
        animals = ['Aardvark', 'Albatross', 'Alligator', 'Ant', 'Anteater', 'Antelope', 'Ape', 'Armadillo', 'Donkey', 'Baboon', 'Badger', 'Barracuda', 'Bat', 'Bear', 'Beaver', 'Bee', 'Bison', 'Boar', 'Buffalo', 'Butterfly', 'Camel', 'Caribou', 'Cat', 'Caterpillar', 'Cheetah', 'Chicken', 'Chimpanzee', 'Clam', 'Cobra', 'Cod', 'Coyote', 'Crab', 'Crane', 'Crocodile', 'Crow', 'Deer', 'Dinosaur', 'Dog', 'Dolphin', 'Dove', 'Eagle', 'Eel', 'Elephant', 'Elk', 'Emu', 'Falcon', 'Ferret', 'Finch', 'Fish', 'Flamingo', 'Fox', 'Frog', 'Gazelle', 'Gerbil', 'Giraffe', 'Goat', 'Goose', 'Gorilla', 'Grasshopper', 'Hamster', 'Hawk', 'Hedgehog', 'Heron', 'Herring', 'Hippo', 'Hornet', 'Hummingbird', 'Hyena', 'Jaguar', 'Jellyfish', 'Kangaroo', 'Koala', 'Lark', 'Lemur', 'Leopard', 'Lion', 'Llama', 'Lobster', 'Mole', 'Mongoose', 'Mouse', 'Mosquito', 'Mule', 'Newt', 'Octopus', 'Ostrich', 'Otter', 'Owl', 'Oyster', 'Panther', 'Parrot', 'Pelican', 'Penguin', 'Pig', 'Pigeon', 'Pony', 'Porcupine', 'Porpoise', 'Quail', 'Rabbit', 'Raccoon', 'Ram', 'Rat', 'Raven', 'Reindeer', 'Rhino', 'Salamander', 'Salmon', 'Sardine', 'Scorpion', 'Seahorse', 'Seal', 'Shark', 'Sheep', 'Snail', 'Snake', 'Sparrow', 'Squis', 'Squirrel', 'Tiger', 'Toad', 'Trout', 'Turkey', 'Turtle', 'Weasel', 'Whale', 'Wolf', 'Zebra']
        nationalities = ['Afghan', 'Albanian', 'Algerian', 'American', 'Andorran', 'Angolan', 'Argentian', 'Armenian', 'Aruban', 'Australian', 'Austrian', 'Bahamian', 'Bahraini', 'Bangladeshi', 'Barbadian', 'Belarusian', 'Belgian', 'Belizean', 'Bermudian', 'Brazilian', 'British', 'Bulgarian', 'Cambodian', 'Cameroonian', 'Canadian', 'Catalan', 'Chadian', 'Chilean', 'Chinese', 'Colombian', 'Croatian', 'Cuban', 'Czech', 'Danish', 'Dominican', 'Dutch', 'Ecuadorian', 'Egyptian', 'English', 'Eritrean', 'Estonian', 'Ethiopian', 'Finnish', 'Fijian', 'Filipino', 'Georgian', 'German', 'Ghanaian', 'Greek', 'Grenadian', 'Guatemalan', 'Guinean', 'Guyanes', 'Haitian', 'Honduran', 'Hungarian', 'Icelandic', 'Indian', 'Indonesian', 'Iranian', 'Irish', 'Israeli', 'Italian', 'Jamaican', 'Japanese', 'Jordanian', 'Kenyan', 'Korean', 'Latvian', 'Lebanese', 'Liberian', 'Libyan', 'Lithuanian', 'Luxembourgish', 'Macedonian', 'Malaysian', 'Maldivian', 'Mauritian', 'Mexican', 'Moroccan', 'Mongolian', 'Namibian', 'Nicaraguan', 'Nigerian', 'Norwegian', 'Pakistani', 'Palestinian', 'Panamanian', 'Paraguayan', 'Peruvian', 'Polish', 'Portuguese', 'Romanian', 'Russian', 'Rwandan', 'Salvadoran', 'Saudi', 'Scottish', 'Senegalese', 'Serbian', 'Singaporean', 'Slovak', 'Slovenian', 'Somali', 'Spanish', 'Sudanese', 'Swedish', 'Swiss', 'Syrian', 'Taiwanese', 'Tanzanian', 'Thai', 'Tibetan', 'Trinidadian', 'Tunisian', 'Turkish', 'Tuvaluan', 'Ugandan', 'Ukrainian', 'Uruguayan', 'Uzbek', 'Vanuatuan', 'Venezuelan', 'Vietnamese', 'Welsh', 'Yemeni', 'Zambian', 'Zimbabwean']
        adjectives = ['Marvelous', 'Insightful', 'Triumphant', 'Scintillating', 'Oscillating', 'Prestigious', 'Pristine', 'Striking', 'Beautiful', 'Elegant', 'Brilliant', 'Gorgeous', 'Agreeable', 'Wonderful', 'Magnificent', 'Vivacious', 'Victorious', 'Energetic', 'Thundering', 'Resonant', 'Successful', 'Exuberant', 'Cheerful', 'Cooperative', 'Rambunctious', 'Playful', 'Innovative', 'Organic', 'Tasty', 'Tasteful', 'Ludacris']

        isUnique = False
        while not isUnique:
            userName = random.choice(adjectives)+random.choice(colors)+random.choice(nationalities)+random.choice(animals)
            if MongoInstance.client['quantify'].users.find({"userName":userName}).count() == 0:
                isUnique = True



        doc = {'uID': userName, "origin": pID, "createDate":int(time.time()), "userData": {}}
        
        MongoInstance.client['quantify']['users'].insert(doc)
        del doc['_id'] 

        results.append(doc)
        return results

    def getUserData(self, pID, uID):
        try:
            return MongoInstance.client['quantify'].users.find_one({'uID': uID})['userData'][pID]
        except:
            return "No project data found"
        # return MongoInstance.client['quantify'].users.find_one({'uID': uID}, {'_id': 0})
        # return pID

    def putUserData(self, pID, uID, user_data):
        updateFields = {}
        data = json.loads(user_data)
        for arg in data:
            if data[arg] != None:
                updateFields['userData.'+pID+'.'+arg] = data[arg]

        insertResult = MongoInstance.client['quantify'].users.update({'uID':uID}, {"$set": updateFields}, upsert=False)
        if insertResult["ok"]:
            return MongoInstance.client['quantify'].users.find_one({'uID': uID})['userData'][pID]
        else:
            return "Error: userData not succesfully updated"

    def getAccount(self, user, pwHash):
        # Returns true if an entry exists with the given uID and pwHash
        lowerUser = user.lower()
        return MongoInstance.client['quantify'].accounts.find_one({'user': lowerUser, 'pwHash':pwHash}) != None

    def postAccount(self, user, pwHash):
        # Returns true if an entry exists with the given uID and pwHash
        lowerUser = user.lower()
        
        if MongoInstance.client['quantify'].accounts.find_one({'user': lowerUser}) != None:
            return False
        else:
            print MongoInstance.client['quantify'].accounts.insert({'user': lowerUser, 'pwHash':pwHash, 'accountData':{'projects':[]}})
            return True
    

    def deleteAccount(self, user, pwHash):
        # Returns true if an entry exists with the given uID and pwHash
        lowerUser = user.lower()
        
        if MongoInstance.client['quantify'].accounts.find_one({'user': lowerUser, 'pwHash':pwHash}) == None:
            print "Username (email) does not exist"
            return False
        else:
            result = MongoInstance.client['quantify'].accounts.remove({'user': lowerUser, 'pwHash':pwHash})
            print result
            if result['ok']:
                print 'Account Deleted'
                return True

    def getAccountData(self, user, pwHash):
        lowerUser = user.lower()
        try:
            return MongoInstance.client['quantify'].accounts.find_one({'user': lowerUser, 'pwHash':pwHash})['accountData']
        except:
            return "No project data found or wrong password"
        # return MongoInstance.client['quantify'].users.find_one({'uID': uID}, {'_id': 0})
        # return pID

    def postAccountData(self, user, pwHash, account_data):
        lowerUser = user.lower()
        data = json.loads(account_data)

        insertResult = MongoInstance.client['quantify'].accounts.update({'user': lowerUser, 'pwHash':pwHash}, {"$set": {'accountData': data}}, upsert=False)
        if insertResult["ok"]:
            return MongoInstance.client['quantify'].accounts.find_one({'user': lowerUser, 'pwHash':pwHash})['accountData']
        else:
            return "Error: userData not succesfully updated"


    ############################
    # Generic Get and Delete for content, metrics, votes
    ############################
    def getThing(self, pID, collectionName, thingIDs):
        db = MongoInstance.client[pID]

        # All IDs, except for pIDs, are really ObjectID strings. Convert all of the thingIDs to an 
        # ObjectID so that they can be passed in bulk to the mongo query.
        objectIDs = []
        for thingID in thingIDs:
            objectIDs.append(ObjectId(thingID))

        return formatObjectIDs(collectionName,[x for x in MongoInstance.client[pID][collectionName].find({'_id':{"$in":objectIDs}})])

    def deleteThing(self, pID, collectionName, thingIDs):
        db = MongoInstance.client[pID]

        # All IDs, except for pIDs, are really ObjectID strings. Convert all of the thingIDs to an 
        # ObjectID so that they can be passed in bulk to the mongo query.
        objectIDs = []
        for thingID in thingIDs:
            objectIDs.append(ObjectId(thingID))

        print MongoInstance.client[pID][collectionName].remove({'_id':{"$in":objectIDs}})
        return {'deleted': True}


    ############################
    # Content
    ############################
    # getContent handled by getThing
    # deleteContent handled by deleteThing

    def postContent(self, pID, **kwargs):
        db = MongoInstance.client[pID]

        content = kwargs['content']
        content_type = kwargs['content_type']
        content_data = kwargs['content_data']
        indexNum = db['content'].find().count()
        cID = str(db['content'].insert({'content_type': content_type, 'content':content, 'content_data': eval(content_data), 'index':indexNum}))        
        db['content'].ensure_index([('index', pymongo.ASCENDING)])
        # If the content isn't simple text, it is a URL - and we shall store it
        if content_type != 'text':
            if not os.path.exists("content/"+pID):
                os.makedirs("content/"+pID)

            try:
                filename = "content/"+pID+"/"+cID+"."+content_type
                urllib.urlretrieve(content, filename)
            except:
                bunkVar = 0

        return cID

    ############################
    # ContentByIndex
    ############################
    def getContentByIndex(self, pID, index):
        db = MongoInstance.client[pID]

        objectIDs = []
        for thingID in index:
            objectIDs.append(int(thingID))
        print objectIDs
        return formatObjectIDs('content',[x for x in MongoInstance.client[pID]['content'].find({'index':{"$in":objectIDs}})])



    ############################
    # Metrics
    ############################
    # getMetrics handled by getThing
    # deleteMetrics handled by deleteThing

    def postMetric(self, pID, **kwargs): 
        db = MongoInstance.client[pID]
        if 'scores' in db.collection_names():
            return "Scores have been run. Can't add new metrics."
        else:
            metric_name = kwargs['metric_name']
            metric_prefix = kwargs['metric_prefix']

            mID = str(db['metrics'].insert({'metric': metric_name, 'metric_prefix':metric_prefix}))
            return mID

    ############################
    # Votes
    ############################
    # getVotes handled by getThing
    # deleteVotes handled by deleteThing
   
    def postVote(self, pID, **kwargs): 
        db = MongoInstance.client[pID]

        mID = kwargs['mID'] 
        vote_result = kwargs['vote_result']
        voter_ip = kwargs['voter_ip']
        uID = kwargs['uID']
        vote_data = kwargs['vote_data']            
        submit_time = time.time()

        vID = str(db['votes'].insert({'mID':mID, 'vote_result': eval(vote_result), 'voter_ip':voter_ip, 'uID':uID, 'vote_data':vote_data, 'submit_time':submit_time, 'flagged':False, 'user_flagged':False}))
        return vID

    def getUserVotes(self, pID, uID, limit):
        if limit == '0':
            return formatObjectIDs('vote',[x for x in MongoInstance.client[pID]['votes'].find({'uID':uID}).sort('_id',-1)])
        else:
            return formatObjectIDs('vote',[x for x in MongoInstance.client[pID]['votes'].find({'uID':uID}).sort('_id',-1).limit(int(limit))])
        



    
    ############################
    # Contestants, Results, Scores, Search
    ############################

    # TODO: Don't return the index number!
    def getContestants(self, pID, mID, num_desired_contestants, mode):
        if mode == 'random':
            numContent = MongoInstance.client[pID]['content'].find().count()
            try:
                randNums = random.sample(range(numContent), num_desired_contestants)
            except:
                randNums = range(numContent)
            return formatObjectIDs('content',[x for x in MongoInstance.client[pID]['content'].find({'index': { '$in': randNums}})])
        elif mode == 'weighted':
            cIDs = set()

            while len(cIDs) < num_desired_contestants:
                threshold = [random.triangular(0,1,1),0] # Generates a random num weighted linearly towards 1.0
                cID = MongoInstance.client[pID]['scores'].find_one({"votability."+mID: {"$near": threshold}})['cID']
                if cID not in cIDs:
                    cIDs.add(cID)
                    # print "result has " +str(MongoInstance.client[pID]['scores'].find_one({"votability."+mID: {"$near": threshold}})['votability'][mID])
            objectIDs = []
            for cID in cIDs:
                objectIDs.append(ObjectId(cID))
            return formatObjectIDs('content',[x for x in MongoInstance.client[pID]['content'].find({ '_id': { '$in': objectIDs}})])

        else:
            return "Invalid Mode Entered"

    def getScores(self, pID, cIDs):
        scores = MongoInstance.client[pID].scores.find({ 'cID': { '$in': cIDs}}, {'cID': 1, 'scores': 1, 'num_votes':1, 'ranks':1, 'parameters':1,'num_ties':1})
        scoreVectors = [{'cID': item['cID'], 'scoreVector': item['scores'], 'numVotes':  item['num_votes'], 'ranks':item['ranks'], 'parameters': item['parameters'], 'numTies':item['num_ties']} for item in scores]
        return scoreVectors

    # TODO Not quite good - we need to build it so that you don't need to query by cIDs. just return the content along with the score in a single object.
    def getResults(self, pID, mID, sort, skip, limit):
        if sort == 1: #If we're returning the best ranked first
            startRank = 0 + skip
            endRank = startRank + limit -1
            print "startRank is " + str(startRank)
            print "endRank is " + str(endRank)
        else:
            numResults = MongoInstance.client[pID].scores.find().count()
            endRank = numResults-1-skip
            startRank = endRank-limit+1

        # TODO
        # Do we want to include a continuation URL? Other metadata (like the skip and limit values used)?
        sorted_results = {}
        results = {}
        sorted_results['query_parameters'] = {}
        sorted_results['query_parameters']['mID'] = mID
        sorted_results['query_parameters']['sort'] = sort
        sorted_results['query_parameters']['skip'] = skip
        sorted_results['query_parameters']['limit'] = limit

        # Get all scores
        scores = [x for x in MongoInstance.client[pID].scores.find({'ranks.'+mID: {'$gte': startRank, '$lte': endRank}}, {'cID': 1, 'ranks.'+mID: 1, 'parameters.'+mID:1,'_id':0}).sort('ranks.'+mID, sort)]

        # Build objectID and cID arrays for the results        
        objectIDs = [];
        cIDs = [];
        for score in scores:
            objectIDs.append(ObjectId(score['cID']))
            cIDs.append(score['cID'])

        # Get the content by cID for all results (the scores query doesn't contain this)
        contents = formatObjectIDs('content',[x for x in MongoInstance.client[pID].content.find({'_id':{"$in":objectIDs}})])


        # Compile all the data from content and scores into a single object
        for content in contents:
            
            results[content['cID']] = content
            # if 'index' in results[content['cID']]: del results[content['cID']]['index']

            # print "hereee"
            # print results[content['cID']]
            # print content['cID']
            # print content['content_data']

        for score in scores:
            results[score['cID']]['rank'] = score['ranks'][mID]
            results[score['cID']]['parameters'] = score['parameters'][mID]
            results[score['cID']]['cID'] = score['cID']

        # Prepare and then Sort all the compiled objects into order
        sorted_results['results'] = [{}]*len(results)

        for item in results:
            if sort == 1:
                sorted_results['results'][results[item]['rank']-skip] = results[item]
            else:
                sorted_results['results'][numResults-results[item]['rank']-skip-1] = results[item]

        return sorted_results
        
    def getDisplayMetrics(self, pID, mode, limit):
        metrics = []
        metricsCursor = MongoInstance.client[pID]['metrics'].find()
        for metric in metricsCursor:
            metrics.append(metric)

        if limit > len(metrics):
            limit = len(metrics)
            
        if mode == "random":
            result = []
            for index in range(limit):
                randIndex = random.randint(0,(len(metrics)-1))
                result.append(metrics[randIndex])
                del metrics[randIndex]
            return formatObjectIDs('metrics',result)

        elif mode == "all":
            return formatObjectIDs('metrics',metrics)

        else:
            return []

    def getSearch(self, pID, search_vector, skip, limit):
        # Build a list of cIDs based on the scores doc
        
        sorted_results = {}
        # results = {}
        sorted_results['query_parameters'] = {}
        sorted_results['query_parameters']['search_vector'] = search_vector
        sorted_results['query_parameters']['search_metrics'] = []
        sorted_results['query_parameters']['search_values'] = []
        for mID, value in search_vector:
            sorted_results['query_parameters']['search_metrics'].append(mID)
            sorted_results['query_parameters']['search_values'].append(value)
        # sorted_results['query_parameters']['sort'] = sort
        sorted_results['query_parameters']['skip'] = skip
        sorted_results['query_parameters']['limit'] = limit

        scores_cursor = MongoInstance.client[pID].scores.find({}, {'cID': 1, 'scores': 1})
        scores = [s for s in scores_cursor if s.get('scores')]  # TODO Ensure all scores have the 'scores' field
        search_results = []
        
        # Calculate distances of each score from input vector
        for s in scores:
            distance_squared = 0
            cID = ObjectId(s['cID'])

            for mID, value in search_vector:
                score_for_metric = s['scores'][mID] / 50.
                distance_squared += (float(value) - score_for_metric) ** 2

            result = {'cID': cID, 'distance': distance_squared}
            search_results.append(result)

        # Sort search results
        # Truncate search results to just what skip+limit demand
        search_results = sorted(search_results, key=lambda s: s['distance'])[skip:(skip+limit)]

        cIDs = [s['cID'] for s in search_results]
        content = formatObjectIDs('content',[x for x in MongoInstance.client[pID].content.find({ '_id': { '$in': cIDs }}, {'_id': 1, 'content': 1, 'content_type': 1, 'content_data': 1, 'index':1} )])

        # Build a dict with the content so we can query the right data when iterating through the results
        contentByCID = {}
        for item in content:
            contentByCID[item['cID']] = item

        max_dist = len(search_vector)

        results = []
        index = 0+skip
        for result in search_results:
            distance = ((max_dist - math.sqrt(result['distance'])) / max_dist)
            cID = str(result['cID'])
            results.append({'cID': cID, 'rank': index, 'parameters':{'distance':distance} , 'content': contentByCID[cID]['content'], 'index': contentByCID[cID]['index'], 'content_type': contentByCID[cID]['content_type'], 'content_data': contentByCID[cID]['content_data']})
            index += 1
            # [{'cID': item['cID'], 'rank': item['rank'], 'distance': result['distance'], 'content': item['content'], 'content_type': item['content_type'], 'content_data': item['content_data']} for result in search_results]
        
        #TODO
        #Add continuation URL and parameters for continuing the search results
        # continuationURL = 'http://gifgif.media.mit.edu/api/search?emotions='+str(emotions_vector).replace(" ", "").replace("'", "")+'&skip='+str(int(skip+limit))+'&limit='+str(limit)
        # print continuationURL
        # parameters = {'continuationURL':continuationURL,'skip':skip,'limit':limit}
        # return {'parameters':parameters,'results':result}
        sorted_results['results'] = results
        return sorted_results

    def getProjectStats(self, pID):
        results = []
        project = MongoInstance.client['quantify'].projects.find_one({'pID':pID})
        numVotes = MongoInstance.client[pID].votes.find().count()
        numContent = MongoInstance.client[pID].content.find().count()
        numMetrics = MongoInstance.client[pID].metrics.find().count()
        dateCreated = project['date_created']
        projectTitle = project['project_title']
        try:
            description = project['description']
        except:
            description = ''

        # privateKey = MongoInstance.client[pID].keys.find({'admin':true})
        # publicKey = MongoInstance.client[pID].keys.find({'admin':false})
        scoresAvailable = 'scores' in MongoInstance.client[pID].collection_names()
        results.append({'projectTitle': projectTitle, 'description':description, 'numVotes': numVotes, 'numContent': numContent, 'numMetrics':numMetrics, 'dateCreated':dateCreated, 'scoresAvailable': scoresAvailable})
        return results


    # def scoresAvailable(self,pID):
    #     return 
         
    def getProjectKeys(self,pID,user,pwHash):

        thisAccount = MongoInstance.client['quantify'].accounts.find_one({'user': user, 'pwHash':pwHash})
        print thisAccount
        validProjects = thisAccount['accountData']['projects']
        if pID in validProjects:
            privateKey = str(MongoInstance.client[pID].keys.find_one({'admin':True})['_id'])
            publicKey = str(MongoInstance.client[pID].keys.find_one({'admin':False})['_id'])
            return {'privateKey':privateKey, 'publicKey': publicKey}
        else:
            return False

        
    # Check if the specified pID exists
    def validPID(self, pID): 
        return pID in MongoInstance.client.database_names() 
        
    # Check if the specified key for a given pID exists
    def validKey(self, pID, key):
        return MongoInstance.client[pID].keys.find_one({'_id': ObjectId(key)}) != None

    # Check if the specified key for a given pID has admin priveleges
    def isAdmin(self, pID, key):
        return MongoInstance.client[pID].keys.find_one({'_id': ObjectId(key)})['admin']




####################
# Scoring Functions
####################
    def initialize_score(self, pID, cID):
        mIDs = getmIDs(pID)
        document = {
            'cID': cID,
            'num_ties': dict([(mID, 0) for mID in mIDs]),
            'num_votes': dict([(mID, 0) for mID in mIDs]),
            'scores': dict([(mID, 25.0) for mID in mIDs]),
            'parameters': dict([(mID, {'mu':25.0, 'sigma':8.333333333333334}) for mID in mIDs]),
            'ranks': dict([(mID, 0) for mID in mIDs]),
            'tie_percentiles': dict([(mID, 0.0) for mID in mIDs]),
            'vote_percentiles': dict([(mID, 0.0) for mID in mIDs]),
            'votability': dict([(mID, [1.0,0]) for mID in mIDs])
        }
        for mID in mIDs:
            MongoInstance.client[pID]['scores'].ensure_index([("votability."+mID, GEO2D)])

        return MongoInstance.client[pID]['scores'].insert(document)

    def setVoteFlagged(self, pID, vID):
        MongoInstance.client[pID]['votes'].update({'_id':ObjectId(vID)}, {"$set":{'flagged':True}}, upsert=False)

    def updateScore(self, pID, cID, mID, new_mu, new_sigma, isTie):
        # Perhaps we should also include a field called 'votability' that we query by.
        MongoInstance.client[pID]['scores'].update(
            {'cID':cID}, 
            {
                "$set":{'scores.'+mID : new_mu, 'parameters.'+mID+'.mu' : new_mu, 'parameters.'+mID+'.sigma' : new_sigma}, 
                "$inc":{'num_ties.'+mID : int(isTie), 'num_votes.'+mID : 1}
            }, 
            upsert=False)
        # print MongoInstance.client[pID]['scores'].find_one({'cID':cID})

    def updatePercentilesAndRanks(self, pID, cID, new_vote_percentiles, new_tie_percentiles, new_ranks, new_votability):
        MongoInstance.client[pID]['scores'].update(
            {'cID':cID}, 
            {
                "$set":{'ranks' : new_ranks, 'vote_percentiles':new_vote_percentiles, 'tie_percentiles':new_tie_percentiles, 'votability':new_votability}
            }, 
            upsert=False)
        # print MongoInstance.client[pID]['scores'].find_one({'cID':cID})

####################



####################
# Build Scores Functions
####################
    def buildScores(self, pID, uID):
        if pID == 'gifgif':
            return False
        elif not uID:
            print "Building scores for " + pID + "..."
            processVotes(self,pID)
            calculatePercentilesAndRanks(self,pID)
            return "Seems to have built scores for " + pID + " succesfully!" 
        else:
            processVotesUser(self,pID,uID)
            calculatePercentilesAndRanksUser(self,pID,uID)
            return "Seems to have built scores for " + uID + " in " +pID+ " succesfully!" 



####################
# User Scoring Functions
####################
    def initialize_score_user(self, pID, uID, cID):
        mIDs = getmIDs(pID)
        document = {
            'cID': cID,
            'uID': uID,
            'num_ties': dict([(mID, 0) for mID in mIDs]),
            'num_votes': dict([(mID, 0) for mID in mIDs]),
            'scores': dict([(mID, 25.0) for mID in mIDs]),
            'parameters': dict([(mID, {'mu':25.0, 'sigma':8.333333333333334}) for mID in mIDs]),
            'ranks': dict([(mID, 0) for mID in mIDs]),
            'tie_percentiles': dict([(mID, 0.0) for mID in mIDs]),
            'vote_percentiles': dict([(mID, 0.0) for mID in mIDs]),
            'votability': dict([(mID, [1.0,0]) for mID in mIDs])
        }
        for mID in mIDs:
            MongoInstance.client[pID]['user_scores'].ensure_index([("votability."+mID, GEO2D)])

        return MongoInstance.client[pID]['user_scores'].insert(document)

    def setVoteFlagged_user(self, pID, vID):
        MongoInstance.client[pID]['votes'].update({'_id':ObjectId(vID)}, {"$set":{'user_flagged':True}}, upsert=False)

    def updateScore_user(self, pID, uID, cID, mID, new_mu, new_sigma, isTie):
        # Perhaps we should also include a field called 'votability' that we query by.
        MongoInstance.client[pID]['user_scores'].update(
            {'cID':cID, 'uID':uID}, 
            {
                "$set":{'scores.'+mID : new_mu, 'parameters.'+mID+'.mu' : new_mu, 'parameters.'+mID+'.sigma' : new_sigma}, 
                "$inc":{'num_ties.'+mID : int(isTie), 'num_votes.'+mID : 1}
            }, 
            upsert=False)
        # print MongoInstance.client[pID]['scores'].find_one({'cID':cID})

    def updatePercentilesAndRanks_user(self, pID, uID, cID, new_vote_percentiles, new_tie_percentiles, new_ranks, new_votability):
        MongoInstance.client[pID]['user_scores'].update(
            {'cID':cID, 'uID':uID}, 
            {
                "$set":{'ranks' : new_ranks, 'vote_percentiles':new_vote_percentiles, 'tie_percentiles':new_tie_percentiles, 'votability':new_votability}
            }, 
            upsert=False)
        # print MongoInstance.client[pID]['scores'].find_one({'cID':cID})

####################

############################
# User-centric Contestants, Results, Scores, Search
############################

    # TODO: Don't return the index number!
    def getContestants_user(self, pID, uID, mID, num_desired_contestants, mode):
        if mode == 'random':
            numContent = MongoInstance.client[pID]['content'].find().count()
            randNums = random.sample(range(numContent), num_desired_contestants)
            return formatObjectIDs('content',[x for x in MongoInstance.client[pID]['content'].find({'index': { '$in': randNums}})])
        elif mode == 'weighted':
            cIDs = set()

            while len(cIDs) < num_desired_contestants:
                threshold = [random.triangular(0,1,1),0] # Generates a random num weighted linearly towards 1.0
                cID = MongoInstance.client[pID]['user_scores'].find_one({"uID":uID, "votability."+mID: {"$near": threshold}})['cID']
                if cID not in cIDs:
                    cIDs.add(cID)
                    # print "result has " +str(MongoInstance.client[pID]['scores'].find_one({"votability."+mID: {"$near": threshold}})['votability'][mID])
            objectIDs = []
            for cID in cIDs:
                objectIDs.append(ObjectId(cID))
            return formatObjectIDs('content',[x for x in MongoInstance.client[pID]['content'].find({ '_id': { '$in': objectIDs}})])

        else:
            return "Invalid Mode Entered"

    def getScores_user(self, pID, uID, cIDs):
        scores = MongoInstance.client[pID].user_scores.find({'uID':uID, 'cID': { '$in': cIDs}}, {'cID': 1, 'scores': 1, 'num_votes':1, 'ranks':1, 'parameters':1,'num_ties':1})
        scoreVectors = [{'cID': item['cID'], 'scoreVector': item['scores'], 'numVotes':  item['num_votes'], 'ranks':item['ranks'], 'parameters': item['parameters'], 'numTies':item['num_ties']} for item in scores]
        return scoreVectors

    # TODO Not quite good - we need to build it so that you don't need to query by cIDs. just return the content along with the score in a single object.
    def getResults_user(self, pID, uID, mID, sort, skip, limit):
        if sort == 1: #If we're returning the best ranked first
            startRank = 0 + skip
            endRank = startRank + limit -1
            print "startRank is " + str(startRank)
            print "endRank is " + str(endRank)
        else:
            numResults = MongoInstance.client[pID].user_scores.find({'uID':uID}).count()
            endRank = numResults-1-skip
            startRank = endRank-limit+1

        # TODO
        # Do we want to include a continuation URL? Other metadata (like the skip and limit values used)?
        sorted_results = {}
        results = {}
        sorted_results['query_parameters'] = {}
        sorted_results['query_parameters']['mID'] = mID
        sorted_results['query_parameters']['sort'] = sort
        sorted_results['query_parameters']['skip'] = skip
        sorted_results['query_parameters']['limit'] = limit

        # Get all scores
        scores = [x for x in MongoInstance.client[pID].user_scores.find({'uID':uID, 'ranks.'+mID: {'$gte': startRank, '$lte': endRank}}, {'cID': 1, 'ranks.'+mID: 1, 'parameters.'+mID:1,'_id':0}).sort('ranks.'+mID, sort)]

        # Build objectID and cID arrays for the results        
        objectIDs = [];
        cIDs = [];
        for score in scores:
            objectIDs.append(ObjectId(score['cID']))
            cIDs.append(score['cID'])

        # Get the content by cID for all results (the scores query doesn't contain this)
        contents = formatObjectIDs('content',[x for x in MongoInstance.client[pID].content.find({'_id':{"$in":objectIDs}})])


        # Compile all the data from content and scores into a single object
        for content in contents:
            
            results[content['cID']] = content
            # if 'index' in results[content['cID']]: del results[content['cID']]['index']
            # print "hereee"
            # print results[content['cID']]
            # print content['cID']
            # print content['content_data']

        for score in scores:
            results[score['cID']]['rank'] = score['ranks'][mID]
            results[score['cID']]['parameters'] = score['parameters'][mID]
            results[score['cID']]['cID'] = score['cID']

        # Prepare and then Sort all the compiled objects into order
        sorted_results['results'] = [{}]*len(results)

        for item in results:
            if sort == 1:
                sorted_results['results'][results[item]['rank']-skip] = results[item]
            else:
                sorted_results['results'][numResults-results[item]['rank']-skip-1] = results[item]

        return sorted_results
        

    def getSearch_user(self, pID, uID, search_vector, skip, limit):
        # Build a list of cIDs based on the scores doc
        
        sorted_results = {}
        # results = {}
        sorted_results['query_parameters'] = {}
        sorted_results['query_parameters']['search_vector'] = search_vector
        sorted_results['query_parameters']['search_metrics'] = []
        sorted_results['query_parameters']['search_values'] = []
        for mID, value in search_vector:
            sorted_results['query_parameters']['search_metrics'].append(mID)
            sorted_results['query_parameters']['search_values'].append(value)
        # sorted_results['query_parameters']['sort'] = sort
        sorted_results['query_parameters']['skip'] = skip
        sorted_results['query_parameters']['limit'] = limit

        scores_cursor = MongoInstance.client[pID].user_scores.find({'uID':uID}, {'cID': 1, 'scores': 1})
        scores = [s for s in scores_cursor if s.get('scores')]  # TODO Ensure all scores have the 'scores' field
        search_results = []
        
        # Calculate distances of each score from input vector
        for s in scores:
            distance_squared = 0
            cID = ObjectId(s['cID'])

            for mID, value in search_vector:
                score_for_metric = s['scores'][mID] / 50.
                distance_squared += (float(value) - score_for_metric) ** 2

            result = {'cID': cID, 'distance': distance_squared}
            search_results.append(result)

        # Sort search results
        # Truncate search results to just what skip+limit demand
        search_results = sorted(search_results, key=lambda s: s['distance'])[skip:(skip+limit)]

        cIDs = [s['cID'] for s in search_results]
        content = formatObjectIDs('content',[x for x in MongoInstance.client[pID].content.find({ '_id': { '$in': cIDs }}, {'_id': 1, 'content': 1, 'content_type': 1, 'content_data': 1, 'index':1} )])

        # Build a dict with the content so we can query the right data when iterating through the results
        contentByCID = {}
        for item in content:
            contentByCID[item['cID']] = item

        max_dist = len(search_vector)

        results = []
        index = 0
        for result in search_results:
            distance = ((max_dist - math.sqrt(result['distance'])) / max_dist)
            cID = str(result['cID'])
            results.append({'cID': cID, 'rank': index, 'parameters':{'distance':distance} , 'content': contentByCID[cID]['content'], 'index': contentByCID[cID]['index'], 'content_type': contentByCID[cID]['content_type'], 'content_data': contentByCID[cID]['content_data']})
            index += 1
            # [{'cID': item['cID'], 'rank': item['rank'], 'distance': result['distance'], 'content': item['content'], 'content_type': item['content_type'], 'content_data': item['content_data']} for result in search_results]
        
        #TODO
        #Add continuation URL and parameters for continuing the search results
        # continuationURL = 'http://gifgif.media.mit.edu/api/search?emotions='+str(emotions_vector).replace(" ", "").replace("'", "")+'&skip='+str(int(skip+limit))+'&limit='+str(limit)
        # print continuationURL
        # parameters = {'continuationURL':continuationURL,'skip':skip,'limit':limit}
        # return {'parameters':parameters,'results':result}
        sorted_results['results'] = results
        return sorted_results

        


        
    # Client corresponding to a single connection
    @property
    def client(self):
        if not hasattr(self, '_client'):
            self._client = pymongo.MongoClient(host='localhost:27017')
            # self._client = pymongo.MongoClient('mongodb://[user]:[password]@quantify-shard-00-00-xznaq.mongodb.net:27017/test?ssl=true&replicaSet=quantify-shard-0&authSource=admin&retryWrites=true')
        return self._client

# A Singleton Object
MongoInstance = mongoInstance()
