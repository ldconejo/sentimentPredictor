# This is the tweet classifier
# MongoDB code based on: http://www.bogotobogo.com/python/MongoDB_PyMongo/python_MongoDB_pyMongo_tutorial_installing.php
# Classifier code based on: http://www.laurentluce.com/posts/twitter-sentiment-analysis-using-python-and-nltk/
import nltk

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

# Extracts all training tweets from DB and turns them into a list
def get_trainingData(db):
    trainingTweets = []
    for trainingTweet in db.trainingTweets.find():
        for key in trainingTweet:
            if key != "_id":
                trainingTweets.append((trainingTweet[key], key))
    return trainingTweets

# Returns a list of all words (including duplicates) in the training set
def get_words_in_tweets(tweets):
    all_words = []
    for (words, sentiment) in tweets:
      all_words.extend(words)
    return all_words

# Returns a set of words, ordered by frequency in the training set
def get_word_features(wordlist):
    wordlist = nltk.FreqDist(wordlist)
    word_features = wordlist.keys()
    return word_features

# Extracts features
def extract_features(document):
    document_words = set(document)
    features = {}
    for word in word_features:
        features['contains(%s)' % word] = (word in document_words)
    return features

# Runs the classifier
def runClassifier(db):
    print("INFO: Starting classifier")
    trainingTweets = get_trainingData(db)

    global word_features
    word_features = get_word_features(get_words_in_tweets(trainingTweets))
    training_set = nltk.classify.apply_features(extract_features, trainingTweets)

    # Train classifier
    global classifier
    classifier = nltk.NaiveBayesClassifier.train(training_set)

    print(classifier.show_most_informative_features(32))

# Classifies a tweet
def classifyTweet(clearTextTweet):
    return classifier.classify(extract_features(clearTextTweet.split()))

