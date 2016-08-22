#!/usr/bin/env python

__copyright__ = "Copyright 2016, Leidos, Inc."
__license__ = "Apache 2.0"
__status__ = "Beta"
__year__ = "2016"

import time
import logging
import os.path
import sys
import json
import requests

from urllib.parse import urlparse, parse_qsl
from nltk.corpus import stopwords

# these thresholds determine whether or not
#     the related variable is considered high or low
# these can be tweaked to alter final results
SCORE_THRESHOLD = 0.5
COUNT_THRESHOLD = 3
RANGE_THRESHOLD = 0.8

TFIDF_SCORE_FILTER = 0.2

class TopicMatcher:
    def __init__(self, domain, modelerlocation, logger):
        r = requests.get(modelerlocation + '/gettfidfs/' + domain)
        self.tfidf = r.json()
        self.logger = logger

    def topic_matching(self, question_words):
        """Match all the question data analysis against the tfidf corpus model"""

        # filter out the stop words
        question_words = [words for words in question_words if words[0].lower() not in stopwords.words('english')]
        # make sure our list is unique
        question_words = list(set(question_words))

        topic_scores = []
        raw_topic_averages = []
        max_count = 0
        for tfidfObj in self.tfidf:
            topic_score = 0
            count = 0
            min_phrase_score = 0
            max_phrase_score = 0
            topic = tfidfObj['topic']
            phrases = tfidfObj['phrases']
            for phrase in phrases:
                if phrase['score'] > TFIDF_SCORE_FILTER:
                    for qword in question_words:
                        qphrase = qword[0]
                        # score is a string, cas to float
                        qword_score = float(qword[1])

                        # if we have a match, average the tfidf score with the question score
                        if qphrase.lower() == phrase['phrase'].lower():
                            topic_score += (phrase['score'] + qword_score) / 2
                            count += 1

                            # find the min and max scores
                            if phrase['score'] > max_phrase_score:
                                max_phrase_score = phrase['score']
                            else:
                                min_phrase_score = phrase['score']

            # find the max number of matches across all topics
            if count > max_count:
                max_count = count

            rnge = max_phrase_score - min_phrase_score

            topic_average = 0 if count == 0 else topic_score / count
            raw_topic_averages.append(dict({'topic': topic, 'average': topic_average, 'count': count, 'range': rnge}))


        # loop through the raw topic averages and adjust them as needed
        for avg in raw_topic_averages:
            topic = avg['topic']
            score = avg['average']
            count = avg['count']
            rnge = avg['range']

            # as part of our algorithm we determine the relative strength index
            rs = 0 if max_count == 0 else (max_count - count) / max_count
            rsi = 1 - (1 / (1 + rs))

            # we need to determine whether the rsi needs to be added or subtracted to the score
            # (right now we're either subtracting or doing nothing)
            rsi_sign = 0
            if score > SCORE_THRESHOLD and count < COUNT_THRESHOLD and rnge < RANGE_THRESHOLD or\
               score < SCORE_THRESHOLD and count > COUNT_THRESHOLD and rnge > RANGE_THRESHOLD or\
               rnge == 0:
                rsi_sign = -1

            master_score = score + (score * rsi * rsi_sign)
            topic_scores.append(dict({'topic': topic, 'score': master_score}))

        sorted_topic_scores = sorted(topic_scores, key=lambda t: t['score'], reverse=True)
        return sorted_topic_scores

if __name__ == '__main__':
    sys.exit()
