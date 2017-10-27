# This is the Twitter client
# Based on code from https://github.com/tweepy/examples/blob/master/streamwatcher.py

from textwrap import TextWrapper
import tweepy
import time
import re

import classifier

class StreamWatcherListener(tweepy.StreamListener):

    status_wrapper = TextWrapper(width=60, initial_indent='    ', subsequent_indent='    ')

    def __init__(self, db):
        tweepy.StreamListener.__init__(self)
        self.db = db

    def on_status(self, status):
        try:
            # This will prevent replies and retweets from being submitted to consideration
            if (not status.retweeted) and ('RT @' not in status.text) and (not status.text.startswith("@")):
                print(self.status_wrapper.fill(status.text))
                print('\n %s  %s  via %s\n' % (status.author.screen_name, status.created_at, status.source))
                self.processTweet(status.text,status.author.screen_name,status.author.id)

                # Tweet should now be submitted for consideration of the user
                # User can select POSITIVE, NEGATIVE, NEUTRAL(??) or BLOCK (to disable tracking of the user who wrote
                # the tweet)

        except KeyboardInterrupt:
            # Catch any unicode errors while printing to console
            # and just ignore them to avoid breaking application.
            pass

    def on_error(self, status_code):
        print('An error has occured! Status code = %s' % status_code)
        return True  # keep stream alive

    def on_timeout(self):
        print('Snoozing Zzzzzz')

    # This method will process a tweet, collect user input and have it all ready to pass it to the database
    def processTweet(self, tweetText, tweetUserScreenName, tweetUserID):
        validReplies = ['YES', 'NO', 'NEUTRAL', 'IGNORE','BLOCK']
        validDecision = False
        while not (validDecision):
            print("TEXT: " + tweetText)
            clearText = self.cleanupTweetText(tweetText)
            print("CLEAR TEXT:" + clearText)
            print("USER: " + tweetUserScreenName)

            # Run tweet through classifier and get its opinion
            prediction = classifier.classifyTweet(clearText)
            print("PREDICTION:" + prediction)
            decision = input("Do you like this tweet?")
            decision = decision.upper()
            decision = decision.strip()
            if decision in validReplies:
                validDecision = True
                if (decision != 'BLOCK')and(decision != 'IGNORE'):
                    tweetWithOpinion = self.__extractWords__(clearText, decision)
                    # Add entry to MongoDB
                    print(tweetWithOpinion[0], tweetWithOpinion[1])
                    classifier.addTrainingTweet(self.db, tweetWithOpinion)
                    print(classifier.get_tweet(self.db))

                    # Retrain the classifier with the new information
                    classifier.runClassifier(self.db)

            else:
                print("ERROR: Invalid reply" + decision)

    # Split tweet's text into words equal or bigger than three words
    def __extractWords__(self, clearText, decision):
        wordsFiltered = [e.lower() for e in clearText.split() if len(e) >= 3]
        result = (wordsFiltered, decision)
        return result


    # This removes any hash signs and links from a Tweets text
    def cleanupTweetText(self, tweetText):
        clearText = ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)"," ",tweetText, re.UNICODE).split())
        return clearText

    # This removes a user from the file and list of users being followed
    def stopFollowing(self, friendsFile):
        pass

# Handles rate limit error
def limit_handled(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            print("WARNING: RateLimit exception, will wait 15 minutes before continuing")
            time.sleep(15 * 60)

# Returns a list of Twitter friends for the account
# Note this method will cause a 15-minute wait since it will exceed the maximum allowed number of calls if you have
# several hundred friends
def listOfFriends(twitterHandle,auth, fileName):
    api = tweepy.API(auth, wait_on_rate_limit=True)
    user = api.get_user(twitterHandle)
    print("My handle is:", user.screen_name)

    # Open destination file
    friendsFile = open(fileName, 'w')

    # get list of friends
    for friend in limit_handled(tweepy.Cursor(api.friends).items()):
        fileLine = friend.screen_name + "," + str(friend.id) + "\n"
        print(fileLine)
        friendsFile.write(fileLine)

    friendsFile.close()

# Opens list of friends and returns a list of IDs
def openListOfFriends(fileName):
    friendFile = open(fileName, 'r')

    friendList = []

    for friend in friendFile:
        friendScreenName, friendID = friend.split(",")
        friendList.append(friendID.strip())

    # Returns a list of friend' IDs
    return friendList

# Import values from key file
def importKeys(fileName):
    file = open(fileName)

    consumer_key = file.readline().strip()
    print(consumer_key)
    consumer_secret = file.readline().strip()
    print(consumer_secret)
    access_token = file.readline().strip()
    print(access_token)
    access_token_secret = file.readline().strip()
    print(access_token_secret)

    return consumer_key, consumer_secret, access_token, access_token_secret


def  launchStreamClient():
    # Consumer keys
    consumer_key, consumer_secret, access_token, access_token_secret = importKeys("keys.txt")
    # Perform authentication
    auth = tweepy.auth.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    # Start DB
    db = classifier.get_db()

    #listOfFriends('ldconejo',auth, "friendlist.csv")
    # Initial training of classifier
    classifier.runClassifier(db)

    # Create stream
    stream = tweepy.Stream(auth, StreamWatcherListener(db), timeout=None)

    # Start stream in sample mode
    #stream.sample()

    # First, get list of friends
    friendList = openListOfFriends("friendlist.csv")

    # Start stream in filter mode
    stream.filter(follow=friendList)