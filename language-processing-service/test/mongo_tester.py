# standard imports
import logging
import os.path
import sys, ast, getopt
import multiprocessing
import datetime as dt

# other libraries
from pymongo import MongoClient
import datetime
from bson.objectid import ObjectId
from mongoaccessor import MongoAccessor

program = os.path.basename(sys.argv[0])
logger = logging.getLogger(program)
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
logging.root.setLevel(level=logging.INFO)
m = MongoAccessor(host='localhost', port=27017, db='DomainModels', collection='CollectionName', verbose=True, logger=logger)
m.getRecordCount()
m.cacheRecords()
m.getRecords()
