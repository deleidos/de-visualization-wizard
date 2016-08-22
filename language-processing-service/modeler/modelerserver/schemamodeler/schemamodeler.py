#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__copyright__ = "Copyright 2016, Leidos, Inc."
__license__ = "Apache 2.0"
__status__ = "Beta"
__year__ = "2016"

description = '''
Adding data sets to the database requires two steps. A top-level description is initially required to capture usage information about a particular data set. Then, the actual schema describing individual data fields should be uploaded. Currently, the system assumes that a data set is the end result of a specific analytic and can be accessed via API or directly.'''
# standard imports
import logging
import os.path
import os
import sys, ast, getopt
import multiprocessing
import datetime as dt
import json
import pprint

# other libraries
from sklearn.feature_extraction.text import TfidfVectorizer

# local imports in this package
from modelerserver.mongoaccessor.mongoaccessor import MongoAccessor # , GridFSModel

help_message = ('''
****************************************************************************************************
* %s                                                                                 *
* Data Sets                                                                                        *
* Add Data Set	        python schemamodeler.py -a -S "<path to data-set JSON file>"               *
* Add Schema	        python schemamodeler.py -a -s "<path to schema JSON file>"                 *
* List Data Set         python schemamodeler.py -l -S "<name>"                                     *
*                         OR python schemamodeler.py -l -S "<sId>"                                 *
* List All Data Sets	python schemamodeler.py -l                                                 *
* List Schema	        python schemamodeler.py -l -s "<sname>"                                    *
*                         OR python schemamodeler.py -l -s "<sId>"                                 *
* List All Schemas      python schemamodeler.py -l                                                 *
* Delete                python schemamodeler.py -r "<sId>"                                         *
* Add Interpretation	python schemamodeler .py -a -I "<interpretation>"                          *
* Add Interpretations	python schemamodeler .py -a -i "<path to interpretations JSON file>"       *
* List Interpretations	python schemamodeler.py -l -i "<interpretation>"                           *
* Delete Interpretation	python schemamodeler.py -r -i "<interpretation>"                           *
****************************************************************************************************
'''
%
    (sys.argv[0])
)

remove_msg = ('''
%s requires a schema specification
For example:
    python knowledgemodeler.py -d -t "Target Identification"
''' % (sys.argv[0]))
add_flag_msg = ('''
%s requires a schema source file specification
For example:
    python schemamodeler.py -a -S ..\\..\\..\\..\\..\\..\\digitaledge_viz_core\\vizwiz-beta\\back-end\\temp-data\\schemas.json
''' % (sys.argv[0]))

add_flag_description_msg = ('''
%s requires a schemadata and a schema specification.
For example:
python schemamodeler.py -A -D ..\\..\\..\\..\\..\\..\\digitaledge_viz_core\\vizwiz-beta\\back-end\\temp-data\\data-sets.json
''' % (sys.argv[0]))


update_msg = ('''
%s requires a schema specification AND Model must exist
''' % (sys.argv[0]))
list_msg = ('''
%s requires a schema specification
For example:
    python schemamodeler.py -l -S "220a5f58-480e-45c3-8252-b3712d9e6c32"
''' % (sys.argv[0]))

leafNode = ""


class Usage(Exception):
    def __init__(s, value):
        s.value = value

    def __str__(s):
        return repr(s.value)


class RemoveSchemaUsage(Exception):
    def __init__(s, value):
        s.value = value

    def __str__(s):
        return repr(s.value)


class AddSchemaDescriptionUsage(Exception):
    def __init__(s, value):
        s.value = value

    def __str__(s):
        return repr(s.value)


class AddSchemaUsage(Exception):
    def __init__(s, value):
        s.value = value

    def __str__(s):
        return repr(s.value)


class AddTfIdfUsage(Exception):
    def __init__(s, value):
        s.value = value


class ListUsage(Exception):
    def __init__(s, value):
        s.value = value

    def __str__(s):
        return repr(s.value)


class UpdateUsage(Exception):
    def __init__(s, value):
        s.value = value

    def __str__(s):
        return repr(s.value)


TODO = '''
We are removing '.' and '/' should we?
Where best to remove ''
'''


class SchemaDataModeler(object):
    def __init__(s, schema=None, dataset=None
        , mongohost='localhost'
        , interpretationsourcefile=None
        , interpretation=None
        , remove_flag=False, list_flag=False, add_flag=False, new_interpretation=False
                 , logger=None, verbose=False):
        # schema and dataset generally refer to files residing on a file syste
        s.schema = schema
        s.dataset = dataset
        s.interpretation = interpretation
        s.interpretationsourcefile = interpretationsourcefile

        s.schemaId = schema
        s.schemaName = schema
        s.datasetId = dataset
        s.datasetName  = dataset
        s.mongohost = mongohost
        s.remove_flag = remove_flag
        s.list_flag = list_flag
        s.add_flag = add_flag
        s.new_interpretation=new_interpretation


        s.json_data = []
        s.logger = logger
        s.verbose = verbose

        if s.verbose : s.logger.info("\ndataset = " + str(s.dataset) + "\nschema = " + str(s.schema))

        # mongo attributes
        s.maD = MongoAccessor(host=s.mongohost, port='27017', db='vizwiz', collection='DataSets',
                              logger=s.logger)
        s.maS = MongoAccessor(host=s.mongohost, port='27017', db='vizwiz', collection='Schemas',
                              logger=s.logger)

        s.maI = MongoAccessor(host=s.mongohost, port='27017', db='vizwiz', collection='Interpretations',
                          logger=s.logger)

    # TODO write getters and setters in the 'official' best practice
    # see http://stackoverflow.com/questions/2627002/whats-the-pythonic-way-to-use-getters-and-setters

    def setschema(s, t):
        s.schema = t

    def getschema(s):
        return s.schema

    def setdataset(s, c):
        s.dataset = c

    def setdatasetId(s, c):
        s.datasetId = c

    def setdatasetName(s, c):
        s.datasetName = c

    def getdatasetByName(s):
        return s.maD.getRecord({"name": s.datasetname})

    def getdatasetById(s):
        return s.maD.getRecord({"schema_ID": s.datasetId})

    def setschemaId(s, sId):
        s.schemaId = sId
    def setschemaName(s, sName):
        s.schemaName = sName
    def setinterpretation(s, t):
        s.interpretation = t

    def getinterpretation(s):
        return s.interpretation

    def listinterpretation(s, interpretation):
        if interpretation:
            return s.maI.getRecord({"interpretation": interpretation})
        else:
            return s.maI.getRecordsAsString()  # returns the cache of records

    def listschema(s, schema):
        if schema:
            rec = s.maS.getRecord({"sId": schema})
            if rec is not None:return rec
            return s.maS.getRecord({"sName": schema})
        else:
            return s.maS.getRecordsAsString()  # returns the cache of records

    def listdataset(s, dataset):
        if dataset:
            rec = s.maS.getRecord({"schema_ID": dataset})
            if rec is not None:return rec
            return s.maS.getRecord({"name": dataset})
        else:
            return s.maD.getRecordsAsString()  # returns the cache of records

    def removeschema(s):
        if s.schema is not None:
            s.maS.deleteRecord({"sId": s.schema}) # also remove the corresponding data-set record
            s.maD.deleteRecord({"schema_ID": s.schema}) # also remove the corresponding data-set record

    def removeinterpretation(s):
        if s.interpretation is not None:
            s.maI.deleteRecord({"interpretation": s.interpretation}) # also remove the corresponding data-set record

    def adddataset(s):
        enc = 'utf-8'
        try:
            json_data = json.load(open(s.dataset, 'r', encoding=enc)) # here Visualization is indetendto be a JSON file
            if s.verbose : s.logger.info("json_data : " + str(json_data) )
            print("type(d) :", type(json_data))
            if (type(json_data) == str ):
                d = json.loads(json_data)
                print ("type(d) :", type(d) )
                key = d['schema_ID']
                if s.verbose : s.logger.info("Key Value:" + str(key))
                if s.verbose : s.logger.info("Upserting visualization for key :" + str(key))
                s.maV.upsertRecord({"schema_ID": key}
                    , d
                    , upsert=True)
            elif (type(json_data) == type(dict()) ):
                if s.verbose : s.logger.info("JSON_data <json_data>:" + str(json_data))
                key = json_data['schema_ID']
                if s.verbose : s.logger.info("Key Value:" + str(key))
                if s.verbose : s.logger.info("Upserting visualization for key :" + str(key))
                s.maD.upsertRecord({"name": key}
                                       , json_data
                                       , upsert=True)
        except Exception as e:
            print (help_message)
            print(("** %s Exception** %s:") % (sys.argv[0], str(e)) )
            return False


    def addschema(s):
        enc = 'utf-8'

        try:
            json_data = json.load(open(s.schema, 'r', encoding=enc))
        except Exception as e:
            print(help_message)
            print(("** %s Exception** %s:") % (sys.argv[0], str(e)))
            return False
        if s.verbose: s.logger.info("json_data : " + str(json_data) )
        if s.verbose: s.logger.info("type(d) :", str( type(json_data)))
        if type(json_data) == str :
            try:
                d = json.loads(json_data)
                print ("type(d) :", type(d) )
                key = d['sId']
                if s.verbose : s.logger.info("Key Value:" + str(key))
                # get corresponding dataset
                s.setdatasetId ( str(key)  )
                record = s.getdatasetById()
                if record is not None:
                    # upsert a new schema record
                    if s.verbose : s.logger.info("Upserting schema for key :" + str(key))
                    s.maS.upsertRecord({"sId": key}
                                       , d
                                       , upsert=True)
                    return True
                else:
                    s.logger.info("Failed Upserting schema for key :" + str(key) + " No find for corrresponding data set")
                    return False
            except Exception as e:
                print(help_message)
                print(("** %s Exception** %s:") % (sys.argv[0], str(e)))
                return False

        elif type(json_data) == type(dict()) :
            if s.verbose : s.logger.info("JSON_data <json_data>:" + str(json_data))
            key = json_data['sId']
            if s.verbose : s.logger.info("Key Value:" + str(key))
            # get corresponding dataset
            s.setdatasetId ( str(key)  )
            record = s.getdatasetById()
            if record is not None:
                # upsert a new schema record
                if s.verbose : s.logger.info("Upserting schema for key :" + str(key))
                s.maS.upsertRecord({"sId": key}
                                   , json_data
                                   , upsert=True)
                return True
            else:
                s.logger.info("Failed Upserting schema for key :" + str(key) + " No find for corrresponding data set")
                return False

    def createInterpretationFromString(s):
        if s.verbose : s.logger.info("createInterpretationFromString: interpretation : " + s.interpretation)
        # get corresponding dataset
        s.maI.upsertRecord({"interpretation": s.interpretation}
                           , {"interpretation": s.interpretation}
                           , upsert=True)
        return True

    def createInterpretationfromFile(s):
        enc = 'utf-8'
        try:
            json_data = json.load(open(s.interpretationsourcefile, 'r', encoding=enc))
            if s.verbose : s.logger.info("type(d) :" + str(type(json_data)) )

            if s.verbose : s.logger.info("createInterpretationfromFile JSON_data (dict) <json_data>:" + str(json_data))
            key = json_data['interpretations']

            if s.verbose : s.logger.info("Key Value:" + str(key))
            for kvpair in key:
                if s.verbose : s.logger.info("Upserting interpretation :" + str(kvpair['interpretation']))
                s.maI.upsertRecord(  {"interpretation": str(kvpair['interpretation']) }
                                   , {"interpretation": str(kvpair['interpretation']) }
                                   , upsert=True)
            return True
        except Exception as e:
            print (help_message)
            print(("** %s Exception** %s:") % (sys.argv[0], str(e)) )
            return False
    def selfidentify(s):
        s.logger.info("Knowledge Modeler version :" + __version__)


def main(argv=None):
    mongohost = os.environ.get('MONGOHOST')
    if not mongohost:
        mongohost = 'mongo'
    schema = dataset = msg = interpretation = interpretationsourcefile =  None
    verbose = removeflag = listflag = addflag = adddataset = newinterpretation = False

    program = os.path.basename(sys.argv[0])
    logger = logging.getLogger(program)

    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
    logging.root.setLevel(level=logging.INFO)
    ##
    # One may add a data set for schema alone or with a schema to back it
    # The data-set should pre-exist the elabourating schema
    # thus if schemamodeler is invoked for example via
    # python schemamodeler -a -s schemas.json -f data-sets.json
    # the process MUST upsert the data FIRST in the collection datasets, then
    # in upserting the schemas MUST check datasets (key ==> "sId": "220a5f58-480e-45c3-8252-b3712d9e6c32")
    # IF exists, THEN upsert the schema into schemas
    if argv is None:
        argv = sys.argv
        logger.info("running %s" % ' '.join(argv))
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hs:S:I:i:M:rvlaA"
                , ["help", "schema=", "Schemadata=","Interpretation=", "interpretationsourcefile="
                , "MONGOHOST="
                , "removeflag", "verbose", "listflag", "add", "adddataset", "addinterpretation"])
        except (getopt.error, msg):
            raise Usage(help_message)

        # option processing
        for option, value in opts:
            logger.info("Option :" + option + " value :" + value)
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-v", "--verbose"):
                verbose = True
            if option in ("-s", "--schema"):
                schema = value
            if option in ("-S", "--Schemadata"):
                dataset = value
                logger.info("Data Set <" + dataset +">")
            if option in ("-M", "--MONGOHOST"):
                mongohost = value
            if option in ("-r", "--removeflag"):
                removeflag = True
            if option in ("-l", "--listflag"):
                listflag = True
            if option in ("-a", "--add"):
                addflag = True
            if option in ("-A", "--addinterpretation"):
                newinterpretation = True
            if option in ("-I", "--Interpretation"):
                interpretation = value # String
            if option in ("-i", "--interpretationsourcefile"):
                interpretationsourcefile = value

        if (removeflag and (not schema and not interpretation) ): raise RemoveSchemaUsage(remove_msg) # the "dataset" here refers to the data Id string
        if (newinterpretation and    (not interpretation  and not interpretationsourcefile) ): raise AddSchemaUsage(add_flag_msg) # schema and dataset are both files
        if (addflag  and  (not schema and not dataset and not interpretation and not interpretationsourcefile) ):
            raise AddSchemaUsage(add_flag_msg) # schema and dataset are both files

    except Usage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        print("Usage\n\t", help_message, file=sys.stderr)
        return 2
    except RemoveSchemaUsage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("Remove Usage\n\t", remove_msg, file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        return 2
    except AddSchemaDescriptionUsage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("New Model Usage\n\t", add_flag_description_msg, file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        return 2
    except AddSchemaUsage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("Add Usage\n\t", add_flag_msg, file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        return 2
    except ListUsage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("List Usage\n\t", list_msg, file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        return 2

    t = SchemaDataModeler(
        schema=schema, dataset=dataset
        , mongohost=mongohost
        , interpretationsourcefile=interpretationsourcefile
        , interpretation=interpretation
        , list_flag=listflag
        , remove_flag=removeflag
        , add_flag=addflag
        , new_interpretation=newinterpretation
        , logger=logger, verbose=verbose)
    if t.remove_flag:
        if (schema is not None):
            t.setschema(schema)
            logger.info("Deleting Schema = " + t.getschema())
            t.removeschema()
        if (interpretation is not None):
            t.setinterpretation(interpretation)
            logger.info("Deleting Interpretation = " + t.getinterpretation())
            t.removeinterpretation()

        return
    if t.add_flag:
        if t.schema is not None:
            logger.info("Creating/Updating Schema = " + t.schema)
            t.addschema()
            return
        if t.dataset is not None:
            logger.info("Adding/Updating dataset = " + t.dataset)
            t.adddataset()
            return
        if t.interpretation:
            t.createInterpretationFromString()
            return
        if t.interpretationsourcefile:
            t.createInterpretationfromFile()
            return

    if t.new_interpretation:
        if t.interpretation:
            t.createInterpretationFromString()
        if t.interpretationsourcefile:
            t.createInterpretationfromFile()
        return
    if t.list_flag:  #
        if t.schema is not None:
            logger.info("Finding/Schema = " + str(t.schema) )
            s = t.listschema(t.schema)
            logger.info("Schema Records >>\n" + str(json.dumps(s, indent=4, sort_keys=True)))
            return
        elif t.dataset is not None:
            d = t.listdataset(t.schema)
            logger.info("DataSet Records >>\n" + str(json.dumps(d, indent=4, sort_keys=True)))
            return
        elif t.interpretation is not None:
            d = t.listinterpretation(t.interpretation)
            logger.info("Interpretation Records >>\n" + str(json.dumps(d, indent=4, sort_keys=True)))
            return
        else:
            logger.info("Finding/Schema = " + str(t.schema) )
            s = t.listschema(t.schema)
            logger.info("Schema Records >>\n" + str(json.dumps(s, indent=4, sort_keys=True)))
            d = t.listdataset(t.schema)
            logger.info("DataSet Records >>\n" + str(json.dumps(d, indent=4, sort_keys=True)))
            d = t.listinterpretation(t.interpretation)
            logger.info("Interpretation Records >>\n" + str(json.dumps(d, indent=4, sort_keys=True)))
            return




if __name__ == "__main__":
    sys.exit(main())
