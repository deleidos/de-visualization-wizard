#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__copyright__ = "Copyright 2016, Leidos, Inc."
__license__ = "Apache 2.0"
__status__ = "Beta"
__year__ = "2016"

# standard imports
import logging
import os.path
import sys, ast, getopt
import multiprocessing
import datetime as dt

# other libraries
#from gensim.corpora import WikiCorpus
import gensim
from gensim.models import Word2Vec
from gensim.models.word2vec import LineSentence
# local imports in this package

gHTMLSeparator = '%20'
gHTMLSeparator0 = '&'
description = '''
This module will intake an exsiting a model which is written to the local files system
or in a MongoDB for later use.
It will process to discover the most similar terms and return them
'''
help_message = ('''
Typical use:
%s -v {True | False} -s <file source> -m <model output file> -w <word2vec output file> -t {True | False}
    or
%s  --verbose={True | False}  --source=<file source> --model=<model output file> --word2vec=<word2vec output file> --trainingmode={True | False}
Thus
python w2vmodel.py -v True -s 500.txt -m model_output -w w2v_output -t True
would be a decent invocation
''' % (sys.argv[0], sys.argv[0]))

class Usage (Exception):
  def __init__(s, value):
    s.value = value
  def __str__(s):
    return repr(s.value)

class W2VModels (object):
    def __init__(s, modelName=None, model=None, modelstore=None, logger=None, verbose=False):
        s.logger = logger
        s.modelstore = modelstore
        s.model = model
        if s.model is None:
            s.logger.error("Model '{}' does not exist. unable to continue".format(modelName))
            raise Usage(help_message)

        s.logger = logger
        s.verbose = verbose
        s.terms = ['*']
        s.lineSentence = None
        s.sentences = []

    def setModel(s, modelstore):
        s.modelstore = modelstore
        # if file exists use it to populate model, else read, process, then store it for future use
        if os.path.exists(s.modelstore):
            s.existingModel = True
            s.logger.info("\n###\n## model : " + s.modelstore + " loading ...\n##\n")
            s.model = Word2Vec.load(s.modelstore)
            s.logger.info("\n###\n## model : " + s.modelstore + " ... loaded\n##\n")
            return True
        else:
            s.model = None
            return False
    def getModel(s):
        return s.modelstore

    def setTerms(s, term):
        s.terms = term.split(gHTMLSeparator0)
        s.terms = list(filter(('').__ne__, s.terms))
        s.logger.info("setTerms >> " + str(s.terms) )
        print("setTerms >> " + str(s.terms) )

    def getTerms(s):
        return (str(s.terms) )
    def process(s):
        start = dt.datetime.now()
        topn = 10
        most_similar_words = []
        try:
            most_similar_words = s.model.most_similar(positive=s.terms, topn=topn)
            finish = dt.datetime.now()
            s.logger.info("Finished Processing. Elapsed time : " + str( (finish-start).microseconds / 1000))
            return most_similar_words
        except KeyError as e:
            finish = dt.datetime.now()
            s.logger.info("*Error*:" + str(e) + " Finished Processing. Elapsed time : " + str( (finish-start).microseconds / 1000))
            most_similar_words.append ({'*ERROR*' :str(e)})
            return most_similar_words

    def selfIdentify(s):
        s.logger.info("W2VModels version :" + __version__)

def main(argv=None, testMode=False):
    model = wkp = msg = None
    verbose = trainingmode = False
    arguments = {}

    program = os.path.basename(sys.argv[0])
    logger = logging.getLogger(program)

    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
    logging.root.setLevel(level=logging.INFO)

    if argv is None:
        argv = sys.argv
        logger.info("running %s" % ' '.join(argv))
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hm:t:v:", ["help", "modelstore=", "testmode=""verbose="])
        except (getopt.error, msg):
            raise Usage(help_message)

        # option processing
        for option, value in opts:
            if option in ("-v", "--verbose"):
                verbose = ast.literal_eval(str(value.title()))
            if option in ("-t", "--testmode"):
                testmode = ast.literal_eval(str(value.title()))
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-m", "--model"):
                modelstore = value

        if modelstore is None:
            raise Usage(help_message)


    except Usage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("Usage\n\t", help_message, file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        return 2


    if modelstore is not None:
        print("\tmodel =", modelstore, file=sys.stderr)
        wkp = W2VModels( modelstore=modelstore,logger=logger, verbose=verbose)
        if (testmode):
            wkp.setTerms('city' + gHTMLSeparator + 'town' + gHTMLSeparator0 + 'village') # for a testdata term
            most_similar_words = wkp.process()
            logger.info("Test: most_similar_words :", most_similar_words)
    else:
        raise Usage(help_message)
if __name__ == "__main__":
    sys.exit(main())
