#!/usr/bin/env python

__copyright__ = "Copyright 2016, Leidos, Inc."
__license__ = "Apache 2.0"
__status__ = "Beta"
__year__ = "2016"

import sys
import nltk
import requests
from nltk.util import bigrams, trigrams
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import wordnet as wn

from .spellingcorrector import SpellingCorrector

class QuestionAnalyzer:
    def __init__(self, question, modelerlocation, logger=None):
        self.question = question
        self.tokens = [word.lower() for word in nltk.word_tokenize(self.question)]
        self.tagged = nltk.pos_tag(self.tokens)
        self.modelerlocation = modelerlocation
        r = requests.get(modelerlocation + '/getquestionterms')
        self.wh_terms = r.json()

    def getTenses(self):
        """Find the number of tense indicating words there are in the question"""
        past = len([word for word in self.tagged if word[1] in ["VBD", "VBN"]])
        present = len([word for word in self.tagged if word[1] in ["VBP", "VBZ","VBG"]])
        future = len([word for word in self.tagged if word[1] == "MD"])
        return (past, present, future)

    def getNgrams(self):
        """Get ngrams from the question. Right now only bigrams and trigrams are supported"""
        bigram_str = [bigram[0] + ' ' + bigram[1] for bigram in bigrams(self.tokens)]
        trigram_str = [trigram[0] + ' ' + trigram[1] + ' ' + trigram[2] for trigram in trigrams(self.tokens)]
        return (bigram_str, trigram_str)

    def getWhTerms(self):
        """Find wh terms at the beginning of the question which might indicate intent"""
        whTerms = []
        for t in self.tagged:
            word, pos = t[0], t[1]
            if pos in ['WP', 'WP$', 'WRB', 'WDT', 'MD']:
                whTerms.append(word)

        return whTerms

    def getAnalyticType(self, tenses, whTerms):
        """Find the question's analytical type based on the tenses and wh terms in the question"""
        keyTerm = ''
        if len(whTerms) > 0:
            keyTerm = whTerms[0].lower()

        analyticType = 'None'
        past = tenses[0]
        present = tenses[1]
        future = tenses[2]

        if past > 0 or present > 0 and future == 0:
            if keyTerm in ['who', 'what', 'where', 'when']:
                analyticType = 'Descriptive'
            if keyTerm in ['why']:
                analyticType = 'Diagnostic'
        if past == 0 and future > 0:
            if keyTerm in ['who', 'what', 'where', 'when', 'will']:
                analyticType = 'Predictive'
        if past == 0 and present > 0 and future > 0:
            if keyTerm in ['how', 'will']:
                analyticType = 'Causal'

        return analyticType

    def getWhAnalysis(self):
        """Analyze the question to rank up or down certain viz types"""
        checkWord = self.tagged[0][0].lower()
        checkWordTwo = ''
        counter = 0
        if len(self.tagged) > 1:
            checkWordTwo = self.tagged[1][0].lower()

        whdict = self.wh_terms
        analysis = {}
        for i in range(len(whdict)):
            if whdict[i]['word'] == checkWord:
                if checkWord == 'how':
                    for phrase in whdict[i]['secondary']:
                        if checkWordTwo == phrase['word']:
                            analysis['word'] = whdict[i]['word'] + ' ' + checkWordTwo
                            analysis['qtype'] = whdict[i]['type']
                            analysis['pos'] = self.tagged[0][1]
                            analysis['rankUp'] = whdict[i]['secondary'][counter]['rankUp']
                            analysis['rankDown'] = whdict[i]['secondary'][counter]['rankDown']
                    break
                else:
                    analysis['word'] = whdict[i]['word']
                    analysis['qtype'] = whdict[i]['type']
                    analysis['pos'] = self.tagged[0][1]
                    analysis['rankUp'] = whdict[i]['rankUp']
                    analysis['rankDown'] = whdict[i]['rankDown']
                    break
            else:
                analysis['word'] = '-'
                analysis['qtype'] = '-'
                analysis['pos'] = '-'

        return analysis

    def getLemmas(self):
        """Get stems (lemmas) of tokens in the question"""
        wnl = WordNetLemmatizer()
        lemmas = []
        for token in self.tagged:
            lemma = wnl.lemmatize(token[0], self.penn_to_wn(token[1]))
            lemmas.append(lemma)

        # only return stems that aren't in the original question
        return list(set(lemmas) - set(self.tokens))

    def correctSpelling(self):
        sc = SpellingCorrector(self.modelerlocation)
        corrected_words = []
        for t in self.tokens:
            corrected = sc.correct(t)
            if corrected != t:
                corrected_words.append(dict({'orig': t, 'corrected': corrected}))

        return corrected_words

    def penn_to_wn(s, tag):
        """Retrieve the WordNet pos tag from the Penn treebank pos tags for the lemmatizer"""
        if 'NN' in tag:
            return wn.NOUN
        elif 'VB' in tag:
            return wn.VERB
        elif 'RB' in tag:
            return wn.ADV
        elif 'JJ' in tag:
            return wn.ADJ
        else:
            return wn.NOUN

if __name__ == "__main__":
    sys.exit()
