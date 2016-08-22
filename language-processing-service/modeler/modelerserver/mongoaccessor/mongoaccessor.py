#!/usr/bin/env python
# -*- coding: utf-8 -*-

__copyright__ = "Copyright 2016, Leidos, Inc."
__license__ = "Apache 2.0"
__status__ = "Beta"
__year__ = "2016"

# standard imports
import logging
import os.path
import tempfile
import sys, ast, getopt
import multiprocessing
import datetime as dt

# other libraries
from pymongo import MongoClient
import gridfs
import json
from gensim.models import Word2Vec

# local imports in this package

help_message = ('''
Typical use:
%s -v {True | False} -m <mongodb host> -p <mongodb port> -d <database> -c <collection>
    or
%s  --verbose={True | False}  --mongohost=<mongo host> --port=<mongod port> --db=<database> --collection=<collection>
Thus:
python <this file>  -h localhost -p 27017 -d wiki_corpus -c wikipedia
might be a useful invocation
''' % (sys.argv[0], sys.argv[0]))


class Usage(Exception):
    def __init__(s, value):
        s.value = value

    def __str__(s):
        return repr(s.value)


class GridFSModel(object):
    def __init__(s, modelName=None, host=None, port=None, logger=None, verbose=False):
        s.model = None
        s.host = host
        s.port = port
        s.logger = logger
        s.verbose = verbose
        s.modelName = modelName
        s.tmpfilename = s.modelStore = r''
        s.mongodb = 'mongodb://' + str(s.host) + ':' + str(s.port) + "/" + str(s.modelName)
        if s.logger and s.verbose:
            s.logger.info("GridFSModel : MongoDB @ <" + s.mongodb + '>\nmodel <' + s.modelName + '> ')
        s.client = MongoClient(s.mongodb)

    def getModelFromGridFS(s):
        dbnames = s.client.database_names()
        dbExists = False
        if s.modelName in dbnames:
            dbExists = True
        if not dbExists:
            return s.model  # return an empty model

        db = s.client[s.modelName]
        fs = gridfs.GridFS(db)
        if s.verbose : s.logger.info("List --> " + str(fs.list()))
        exists = fs.exists()
        if (exists):
            if s.verbose : s.logger.info("getModelFromGridFS : model :" + s.modelName + " Exists")
        else:
            if s.verbose : s.logger.info("model :" + s.modelName + " Does *not* Exists")
            return s.model  # return an empty model
        if s.verbose : s.logger.info("getModelFromGridFS : Number of files -->" + str(db.fs.files.count()))

        objectid = list(db.fs.files.find())[0]['_id']
        if s.verbose : s.logger.info("getModelFromGridFS : model id :" + str(objectid))
        with fs.get(objectid) as fp_read:
            model_in_memory = fp_read.read()
        if s.verbose : s.logger.info('getModelFromGridFS : model_in_memory size -->' + str(len(model_in_memory)))

        with tempfile.NamedTemporaryFile(delete=False, mode='w+b') as temp:
            temp.write(model_in_memory)
            temp.flush()
            tmpfilename = temp.name
            if s.verbose : s.logger.info("getModelFromGridFS : NamedTemporaryFile -->" + tmpfilename)
            if s.verbose : s.logger.info("getModelFromGridFS : Model size -->" + str(os.path.getsize(tmpfilename)))
            return Word2Vec.load(tmpfilename)

    def getModelFromFileSystem(s, modelStore):
        s.model = Word2Vec.load(modelStore)

    def getModelFromFileSystem(s, modelStore):
        s.model = Word2Vec.load(modelStore)
        return s.model
    def saveModelToGridFS(s, model):
        fp = tempfile.NamedTemporaryFile(delete=False, mode='w+b')
        if s.verbose : s.logger.info("saveModelToGridFS : fp -->" + fp.name)
        model.save(fp.name)
        if s.verbose : s.logger.info("saveModelToGridFS: os.path.getsize( fp.name ) --> "
                      + str(os.path.getsize(fp.name))
                      + " GridFS Model Name --> " + s.modelName
                      )

        db = MongoClient(host=s.host)[s.modelName]
        fs = gridfs.GridFS(db)
        fs.put(fp, filename=s.modelName)
        return True
    def dropModelFromGridFS(s, modelName):
        client = MongoClient(s.host, int(s.port))
        if s.verbose : s.logger.info("dropModelFromGridFS: modelName --> " + str(modelName))
        client.drop_database(modelName)
        return True

    def setModelName(s, modelName):
        s.modelName = modelName
        if s.verbose : s.logger.info("setModelName: modelName set to : " + str(modelName))


    def setHostName(s, h):
        s.host = h
        if s.verbose : s.logger.info("setHostName: Host Name set to : " + str(s.host))


class MongoAccessor(object):
    def __init__(s, host=None, port=None, db=None, collection=None, logger=None, verbose=False):
        s.host = host
        s.port = port
        s.db = db
        s.collection = collection
        s.domain = ''
        s.cache = []
        s.records = None
        s.logger = logger
        s.verbose = verbose
        s.mongodb = 'mongodb://' + str(s.host) + ':' + str(s.port) + "/" + str(s.db)
        if s.verbose : s.logger.info("MongoDB @ <" + s.mongodb + '>\ndatabase <' + s.db + '> collection <' + s.collection + '>')
        s.client = MongoClient(s.mongodb)

    def setDomain(s, domain):
        s.domain = domain

    def getDomain(s):
        return s.domain

    def upsertRecord(s, key, data, upsert=True):
        db = s.client[s.db]
        collection = db[s.collection]
        if s.verbose : s.logger.info("Updateing record :" + str(collection) + "\nkey :" + str(key)
                      + "\ndata : " + str(data))
        collection.update(key, data, upsert=upsert)
        return

    def deleteRecord(s, key):
        db = s.client[s.db]
        collection = db[s.collection]
        if s.verbose : s.logger.info("Deleteing record :<" + str(collection) + "> key :" + str(key))
        collection.remove(key)
        return
    def removeRecord(s, key):
        s.deleteRecord(key)
    def removeCollection(s):
        db = s.client[s.db]
        collection = db[s.collection]
        collection.drop()
    def renameCollection(s, newname):
        db = s.client[s.db]
        collection = db[s.collection]
        if s.verbose : s.logger.info("Renaming collection :<" + str(collection) + "> to ==" + str(newname) )
        collection.rename(newname)

    def getRecordCount(s):
        db = s.client[s.db]
        collection = db[s.collection]
        records = collection.find({}).count()
        return records
    def getRecordCountForQuery(s, query):
        db = s.client[s.db]
        collection = db[s.collection]
        records = collection.find(query).count()
        return records
    def getRecord(s, key):
        db = s.client[s.db]
        collection = db[s.collection]
        return collection.find_one(key, {"_id": 0})

    def getCategoricalRecordCount(s):
        db = s.client[s.db]
        collection = db[s.collection]
        records = collection.find({'domain': s.domain}).count()
        return records

    def cacheRecords(s):
        db = s.client[s.db]
        collection = db[s.collection]
        records = s.getRecordCount()
        s.cache = []
        for record in collection.find({}, {"_id": 0}):
            if s.verbose : s.logger.info("RECORD >>" + str(record))
            s.cache.append(record)
        return len(s.cache)

    def cacheRecordsAsString(s):
        db = s.client[s.db]
        collection = db[s.collection]
        records = s.getRecordCount()
        s.cache = []
        for record in collection.find({}, {"_id": 0}):
            if s.verbose : s.logger.info("RECORD >>" + str(record))
            s.cache.append(str(record))
        return len(s.cache)
    def cacheArticles(s):
        db = s.client[s.db]
        collection = db[s.collection]
        records = s.getRecordCount()
        s.cache = []
        for record in collection.find({'domain': s.domain}, {'body': 1, 'title': 1, 'domain': 1}):
            s.cache.append(record)
        return len(s.cache)

    def getCache(s):
        return s.cache
    def getCollections4DB(s):
        s.client = MongoClient(s.host, int(s.port) )
        s.mongodb = 'mongodb://' + str(s.host) + ':' + str(s.port) + "/" + str(s.db)
        if s.verbose : s.logger.info("MongoDB @ <" + s.mongodb + '>\ndatabase <' + s.db )
        s.client = MongoClient(s.mongodb)
        database = s.client[s.db]
        s.collection = database.collection_names(include_system_collections=False)
        s.records = []
        for collection in s.collection:
            if s.verbose : s.logger.info("Collection: " + str(collection))
            c = database[collection]
            recordsfound = c.find({}, {"_id": 0})
            for record in recordsfound:
                if s.verbose : s.logger.info ("Record >>>\n" + str(json.dumps(record, indent=4, sort_keys=True)))
                s.records.append({"collection" : collection, "record": record})
        return s.records

    def getRecords(s):
        start = dt.datetime.now()
        records = s.getRecordCount()
        if s.verbose : s.logger.info('# records : ' + str(records))
        records = s.cacheRecords()
        if s.verbose : s.logger.info('cache size : ' + str(records))
        finish = dt.datetime.now()
        if s.verbose : s.logger.info("Finished Processing. Elapsed time : " + str((finish - start).microseconds / 1000))

        return s.getCache()
    def getRecordsAsString(s):
        start = dt.datetime.now()
        records = s.getRecordCount()
        if s.verbose : s.logger.info('# records : ' + str(records))
        records = s.cacheRecordsAsString()
        if s.verbose : s.logger.info('cache size : ' + str(records))
        finish = dt.datetime.now()
        if s.verbose : s.logger.info("Finished Processing. Elapsed time : " + str((finish - start).microseconds / 1000))

        return s.getCache()

    def selfIdentify(s):
        s.logger.info("Mongo_Accessor version :" + __version__)




def main(argv=None):
    host = port = wkp = msg = db = collection = None
    verbose = False
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
            opts, args = getopt.getopt(argv[1:], "hm:p:d:c:v",
                                       ["help", "mongohost=", "port=", "db=", "collection=", "verbose="])
        except (getopt.error, msg):
            raise Usage(help_message)

        # option processing
        for option, value in opts:
            if option in ("-v", "--verbose"):
                verbose = True
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-m", "--mongohost"):  # note should be a local file in the file system as well
                host = value
            if option in ("-p", "--port"):
                port = value
            if option in ("-d", "--db"):
                db = value
            if option in ("-c", "--collection"):
                collection = value

        if host is None \
                and port is None \
                and db is None \
                and collection is None:
            raise Usage(help_message)

    except Usage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("Usage\n\t", help_message, file=sys.stderr)
        return 2

    if host is not None \
            and port is not None \
            and db is not None \
            and collection is not None:
        print("\tmongo DB host   = ", host, " mongo DB port =", port, file=sys.stderr)
        wkp = MongoAccessor(host=host, port=port, db=db, collection=collection, logger=logger, verbose=verbose)
        # wkp.getRecords()
        wkp.setDomain('black lives matter')
        print("Number of articles for domain:", wkp.getDomain(), "==>", wkp.cacheArticles())


if __name__ == "__main__":
    sys.exit(main())
