# This is the tweet classifier
# MongoDB code based on: http://www.bogotobogo.com/python/MongoDB_PyMongo/python_MongoDB_pyMongo_tutorial_installing.php
import pymongo


# MongoDB setup

def get_db():
    from pymongo import MongoClient
    client = MongoClient('localhost:27017')
    db = client.sentimentAnalysisDB
    return db


def addTrainingTweet(db, trainingTweet):
    db.trainingTweets.insert({trainingTweet[1]: trainingTweet[0]})


def get_tweet(db):
    return db.trainingTweets.find_one()