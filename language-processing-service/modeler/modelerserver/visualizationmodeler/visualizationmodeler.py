#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__copyright__ = "Copyright 2016, Leidos, Inc."
__license__ = "Apache 2.0"
__status__ = "Beta"
__year__ = "2016"

description = '''
Visualizations are the final required element for vizwiz.
JSON input files should contain the following data:
Field Name                   Values                                      Format    Optional?
name                         Any                                         String    No
analytic_type               "DESCRIPTIVE", "PREDICTIVE", "EXPLORATORY",  String    No
                            "INFERENTIAL", "DIAGNOSTIC", "CAUSAL",
                            "MECHANISTIC","PRESCRIPTIVE"
archetypes[]                Archetype Name (must match)                  String    No
domains[]                   Domain Name (must match)                     String    No
mandatory_interpretations[] Interpretation Name (must match)             String    Yes
                            or "Unknown"
thumbnail                   HTTP Link or Path to a Representative Image  String    No
link                        HTTP Link, Path, or Instructions             String    No
                            to the Visualization
'''
# standard imports
import logging
import os.path
import os
import sys, ast, getopt
import multiprocessing
import datetime as dt
import json
import pprint
import types

# other libraries
from sklearn.feature_extraction.text import TfidfVectorizer

# local imports in this package
from modelerserver.mongoaccessor.mongoaccessor import MongoAccessor # , GridFSModel
help_message = ('''
****************************************************************************************************
* %s                                                                          *
* Visualizations                                                                                   *
* Add Visualization     python visualizationmodeler.py -a -V "<path to visualization JSON file>"   *
* Update Visualization	python visualizationmodeler.py -a -V "<path to visualization JSON file>"   *
* List Visualization	python visualizationmodeler.py -l -v "<visualization name>"                *
* List Visualizations	python visualizationmodeler.py -l                                          *
* Delete Visualization	python visualizationmodeler.py -r -v "<visualization name>"                *
****************************************************************************************************
'''
%
    (sys.argv[0])
)

remove_msg = ('''
%s requires a visualization specification
For example:
    python visualizationmodeler.py -r -v "Predictive Vehicle Map"
''' % (sys.argv[0]))
add_visualization_msg = ('''
%s requires a visualization source file specification
For example:
    python visualizationmodeler.py -a -V ./testdata/testVisualization.JSON
''' % (sys.argv[0]))

update_msg = ('''
%s requires a visualization specification AND Model must exist
''' % (sys.argv[0]))
list_msg = ('''
%s requires a visualization specification
For example:
    python visualizationmodeler.py -l -v "Predictive Vehicle Map"
    OR
    python visualizationmodeler.py -l
    to list all
''' % (sys.argv[0]))

leafNode = ""

class Usage(Exception):
    def __init__(s, value):
        s.value = value

    def __str__(s):
        return repr(s.value)


class DeleteVisualizationUsage(Exception):
    def __init__(s, value):
        s.value = value

    def __str__(s):
        return repr(s.value)


class AddVisualizationUsage(Exception):
    def __init__(s, value):
        s.value = value

    def __str__(s):
        return repr(s.value)

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


class VisualizationDataModeler(object):
    def __init__(s
        , vname=None, Visualization=None
        , mongohost='localhost'
        , remove_visualization=False
        , list_flag=False, list_all=False, add_visualization=False
        , logger=None, verbose=False):
        # visualization generally refers to files residing on a file syste
        s.vname = vname
        s.Visualization = Visualization
        s.mongohost = mongohost
        s.remove_visualization = remove_visualization
        s.list_flag = list_flag
        s.list_all = list_all
        s.add_visualization = add_visualization

        s.json_data = []
        s.logger = logger
        s.verbose = verbose

        if s.verbose : s.logger.info("\nvisualization name = " + str(s.vname) )

        # mongo attributes
        s.maV = MongoAccessor(host=s.mongohost, port='27017', db='vizwiz', collection='Visualizations',
                              logger=s.logger)

    # TODO write getters and setters in the 'official' best practice
    # see http://stackoverflow.com/questions/2627002/whats-the-pythonic-way-to-use-getters-and-setters

    def setvisualization(s, t):
        s.visualization = t

    def getvisualization(s):
        return s.visualization

    def setvisualizationname(s, c):
        s.vname = c
    def getvisualizationname(s):
        return s.vname
    def getvisualizationbyname(s, name):
        return s.listvisualization( name )

    def listvisualization(s, vname):
        if vname:
            return s.maV.getRecord({"name": vname} )
        else:
            return s.maV.getRecordsAsString() # returns the cache of records
    def removevisualization(s):
        if s.vname is not None:
            s.maV.deleteRecord( {"name": s.vname})  # also remove the corresponding data-set record

    def addvisualization(s):
        enc = 'utf-8'

        try:
            json_data = json.load(open(s.Visualization, 'r', encoding=enc)) # here Visualization is indetendto be a JSON file
            # s.logger.info("Need a single visualization!!")        #
            if s.verbose : s.logger.info("JSON_data <json_data>:" + str(json_data))
            key = json_data['name']
            if s.verbose : s.logger.info("Key Value:" + str(key))
            if s.verbose : s.logger.info("Upserting visualization for key :" + str(key))
            s.maV.upsertRecord({"name": key}
                , json_data
                , upsert=True)
        except Exception as e:
            print(help_message)
            print(("** %s Exception** %s:") % (sys.argv[0], str(e)))
            return False


    def selfidentify(s):
        s.logger.info("Visualization Modeler version :" + __version__)


def main(argv=None):
    mongohost = os.environ.get('MONGOHOST')
    if not mongohost:
        mongohost = 'mongo'

    Visualization = vname =  msg = None
    verbose = removevisualization = listflag = listall = addvisualization  = False

    program = os.path.basename(sys.argv[0])
    logger = logging.getLogger(program)

    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
    logging.root.setLevel(level=logging.INFO)
    if argv is None:
        argv = sys.argv
        logger.info("running %s" % ' '.join(argv))
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hV:v:M:rlab"
                , ["help"
                , "Visualization=", "visualizationname="
                ,  "MONGOHOST="
                ,  "removevisualization", "listflag", "addvisualization", "bombastic"])
        except (getopt.error, msg):
            raise Usage(help_message)

        # option processing
        for option, value in opts:
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-b", "--bomabastic"):
                verbose = True
            if option in ("-V", "--Visualization"):
                Visualization = value
            if option in ("-v", "--visualizationname"):
                vname = value
            if option in ("-M", "--MONGOHOST"):
                mongohost = value
            if option in ("-r", "--removevisualization"):
                removevisualization = True
            if option in ("-l", "--listflag"):
                listflag = True
            if option in ("-a", "--addvisualization"):
                addvisualization = True

        if (removevisualization and not vname ): raise DeleteVisualizationUsage(remove_msg)
        # the "visualizationdescription" here refers to the data Id string
        if (addvisualization    and  not Visualization ): raise AddVisualizationUsage(add_visualization_msg)
        # visualization and visualizationdescription are both files
        if (listflag  and  not vname ): listall = True

    except Usage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        print("Usage\n\t", help_message, file=sys.stderr)
        return 2
    except DeleteVisualizationUsage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("Delete Usage\n\t", remove_msg, file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        return 2
    except AddVisualizationUsage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("Add Visualization Usage\n\t", add_visualization_msg, file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        return 2

    t = VisualizationDataModeler(
        vname=vname, Visualization=Visualization
        , mongohost=mongohost
        , list_flag=listflag
        , list_all=listall
        , remove_visualization=removevisualization
        , add_visualization=addvisualization
        , logger=logger, verbose=verbose)

    if t.remove_visualization:
        t.setvisualizationname(vname)
        logger.info("Deleting Visualization = " + t.getvisualizationname())
        t.removevisualization()
        return
    if t.add_visualization:
        logger.info("Creating/Updating Visualization = " + t.Visualization)
        t.addvisualization()
        return

    if t.list_flag:
        tx=None
        if t.vname:
            logger.info("Finding/Visualization = " + str( t.vname) )
            tx = t.listvisualization(t.vname)
            logger.info(">>\n" + str(json.dumps(tx, indent=4, sort_keys=True)))
        return



if __name__ == "__main__":
    sys.exit(main())
