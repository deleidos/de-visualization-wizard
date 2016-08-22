#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__copyright__ = "Copyright 2016, Leidos, Inc."
__license__ = "Apache 2.0"
__status__ = "Beta"
__year__ = "2016"

description = '''
Knowledge models (a/k/a taxonomies) are used to divide a domain into focused subjects or groups.
These sub-classifications allow the application to better link specific data sets and visualizations.
The taxonomy should be designed as a tree, with more vague classifications becoming parent nodes.

Because taxonomies are mapped to specific domains, the command for creating a taxonomy
requires the path to the JSON file and the domain name.
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
from time import gmtime, strftime


# other libraries
from sklearn.feature_extraction.text import TfidfVectorizer

# local imports in this package
from modelerserver.mongoaccessor.mongoaccessor import MongoAccessor , GridFSModel
help_message = ('''
****************************************************************************************************
* %s                                                                              *
* Taxonomies                                                                                       *
* Create a Taxonomy      python knowledgemodeler.py -n -T "<path to taxonomy JSON file>"           *
*                        -D "<domain name>"                                                        *
* Add Corpus to Taxonomy python knowledgemodeler.py -a -D "<domain name>"                          *
*                        -c "<path to corpus JSON file>"                                           *
* Update Taxonomy        python knowledgemodeler.py -n -T "<path to taxonomy JSON file>"           *
* List Taxonomies        python knowledgemodeler.py -l -D "<domain name>"                          *
* Delete Taxonomy        python knowledgemodeler.py -r -D "<domain name>"                          *
* Run tf-idf             python knowledgemodeler.py --tfidf -D "<domain name>"                     *
* List tf-idf            python knowledgemodeler.py -L -D "<domain name>" -c "<leaf node name>"    *
****************************************************************************************************
'''
%
    (sys.argv[0])
)

remove_msg = ('''
%s requires a taxonomy specification:
python knowledgemodeler.py -d
-t <domain name>
# removes db.KnowledgeModelTaxonomy record
# removes KnowledgeModelCorpora records
# removes KnowledgeModelCorpora records

For Example:

python knowledgemodeler.py -r -T "National Security"
''' % (sys.argv[0]))

new_msg = ('''
%s requires a taxonomy specification
    python knowledgemodeler.py
        -n  | --new
    -T <taxonomy specified in JSON file>
For example:
python knowledgemodeler.py -n -T .\data\taxonomysample.json
''' % (sys.argv[0]))

add_msg = ('''
%s requires a corpus and a taxonomy specification.
python knowledgemodeler.py
    -a
    -T <domain>
    -c  <corpus json file>

Example

$ python knowledgemodeler.py
    -a    -T “National Security”    -c  ./data/corpus.json
''' % (sys.argv[0]))


add_tfidf_msg = ('''
%s requires a corpus and a taxonomy specification.
python knowledgemodeler.py
    { --Tfidf | -T }
    -d <domain>

Example

python knowledgemodeler.py --tfidf  -T "National Security"

''' % (sys.argv[0]))

update_msg = ('''
%s requires a taxonomy specification
    python knowledgemodeler.py
        -n  | --new
    -T <taxonomy specified in JSON file>
For example:
python knowledgemodeler.py -n -T .\data\taxonomysample.json
''' % (sys.argv[0]))

list_msg = ('''
python knowledgemodeler.py -l -T <domain name>
OR
python knowledgemodeler.py -l -c <corpus name>
OR
python knowledgemodeler.py –l -T <domain name> -c <corpus name>

For example:
        * python knowledgemodeler.py -l -T "National Security"
        * python knowledgemodeler.py -l -T "National Security" -c "Bed Down"
        * python knowledgemodeler.py -l -T "National Security" -c "Bed Down""
%s requires a schema specification

''' % (sys.argv[0]))
leafNode = ""

class Usage (Exception):
  def __init__(s, value):
    s.value = value
  def __str__(s):
    return repr(s.value)

class DeleteTaxonomyUsage (Exception):
  def __init__(s, value):
    s.value = value
  def __str__(s):
    return repr(s.value)
class NewTaxonomyUsage (Exception):
  def __init__(s, value):
    s.value = value
  def __str__(s):
    return repr(s.value)
class AddUsage (Exception):
  def __init__(s, value):
    s.value = value
  def __str__(s):
    return repr(s.value)
class AddTfIdfUsage (Exception):
    def __init__(s, value):
        s.value = value
class ListUsage (Exception):
  def __init__(s, value):
    s.value = value
  def __str__(s):
    return repr(s.value)

class UpdateUsage (Exception):
  def __init__(s, value):
    s.value = value
  def __str__(s):
    return repr(s.value)
TODO = '''
We are removing '.' and '/' should we?
Where best to remove ''
'''

class KnowledgeModel (object):
    def __init__(s, taxonomysource=None, corpus=None, domain=None
        ,mongohost='localhost'
        ,remove_taxonomy=False, list_flag=False, list_tfidf_flag = False, new_taxonomy=False # <-- note: new also subsumes update if exist
        ,add_corpus=False, add_tfidf=None
        ,logger=None, verbose=False):

        s.taxonomysource = taxonomysource
        s.domain = domain
        s.domaincollection = s.domain
        if s.domain is not None:
            s.domaincollection = s.domain.replace(" ", "_")

        s.corpus = corpus
        s.mongohost = mongohost
        s.remove_taxonomy = remove_taxonomy
        s.new_taxonomy = new_taxonomy
        s.add_corpus = add_corpus
        s.add_tfidf = add_tfidf
        s.list_flag = list_flag
        s.list_tfidf_flag = list_tfidf_flag

        s.json_data = []
        s.logger = logger
        s.verbose = verbose

        if s.verbose : s.logger.info ("\ncorpus = " + str( s.corpus) + "\ntaxonomy domain = " + str( s.domain) )

        # mongo attributes
        s.maD = MongoAccessor(host=mongohost, port='27017', db='vizwiz',  collection='Domains'
                , logger=s.logger)
        if (s.domain is not None):
            if s.verbose : s.logger.info("KnowledgeModelTaxonomy Database for taxonomy domain : " + s.domain )
            s.maT = MongoAccessor(host=s.mongohost, port='27017', db='KnowledgeModelTaxonomy', collection=s.domaincollection
                , logger=s.logger)
        else:
            s.maT = MongoAccessor(host=s.mongohost, port='27017', db='KnowledgeModelTaxonomy', collection=""
                                  , logger=s.logger)
        if (s.domain is not None):
            if s.verbose : s.logger.info("KnowledgeModelCorpora Database for taxonomy domain: " + s.domain )
            s.maC = MongoAccessor(host=s.mongohost, port='27017', db='KnowledgeModelCorpora',collection=s.domaincollection
                ,logger=s.logger)
## Note: ^^^ KnowledgeModelCorpus is a specific DB
# Each collection in this db is a Domain name; thus, KnowledgeModelCorpus.National_Security & .International_Finance
# would be valid
        if (s.domain is not None):
            if s.verbose : s.logger.info("KnowledgeModelTfIdf Database for taxonomy domain: " + s.domain )
            s.maTfIdf = MongoAccessor(host=s.mongohost, port='27017', db='KnowledgeModelTfIdf', collection=s.domaincollection
                ,logger=s.logger)

## Note: ^^^ KnowledgeModelTfIdf is a specific DB
# Each collection in this db is a Domain name; thus,
# KnowledgeModelTfIdf .National_Security and  .International_Finance
# would be valid

    def settaxonomy(s, t): s.taxonomy = t
    def gettaxonomy(s): return s.taxonomy

    def setcorpus(s, c): s.corpus = c
    def getcorpus(s): return s.corpus
    def createtaxonomy(s):
        enc = 'utf-8'
        if s.new_taxonomy:
            try:
                s.json_data = json.load(open(s.taxonomysource, 'r', encoding=enc))
                if s.verbose : s.logger.info("s.domain ==>" +  s.json_data["domain"] )
                s.domaincollection = s.json_data["domain"].replace(' ' , '_')
                if s.verbose : s.logger.info("s.domaincollection ==>" +  s.domaincollection )
                s.maT = MongoAccessor(host=s.mongohost, port='27017', db='KnowledgeModelTaxonomy'
                                      , collection=s.domaincollection
                                      , logger=s.logger)
                records = s.maT.getRecordCount()
                if s.verbose : s.logger.info ("KnowledgeModelTaxonomy records :" + str(records))
                s.maT.upsertRecord({"domain" : s.json_data["domain"]}, s.json_data,  upsert=True )
            except Exception as e:
                print (help_message)
                print(("** %s Exception** %s:") % (sys.argv[0], str(e)) )
                return False
        else:
            raise Usage(help_message)

    def getDomainByName(s):
        return s.maD.getRecord({"domain": s.domain})

    def getDomainByDomain(s):
        return s.getDomainByName()


    def listtaxonomy(s):
        if s.domaincollection:
            record = s.maT.getRecord({"domain": s.domain})
            if s.verbose : s.logger.info("KnowledgeModelTaxonomy record for domain :" + s.domain + " : " + str(record))
            return record

    def listalltaxonomies(s):
        if s.verbose : s.logger.info("listalltaxonomies :" + str(s.domain))
        ma = MongoAccessor(host=s.mongohost, port='27017', db="KnowledgeModelTaxonomy", collection="", logger=s.logger)

        records = ma.getCollections4DB()
        for record in records:
            if s.verbose : s.logger.info("KnowledgeModelTaxonomy record : " + str(record))
        return records

    def listcorpus(s):
        if s.verbose : s.logger.info("listcorpus ")
        if s.corpus:
            record = s.maC.getRecord({"topic": s.corpus})
            return record
        else:
            records = s.maC.getRecordsAsString()
            for record in records:
                if s.verbose : s.logger.info("KnowledgeModeler Corpora record : " + str(record))
    def listtfidf(s):
        # if domain and corpus get single record
        if (s.domain and s.corpus):
            record = s.maTfIdf.getRecord({"term": s.corpus, "domain" : s.domaincollection})
            return record
        else:
            records = s.maTfIdf.getRecords()
            return records

    def removetaxonomy(s):
        #
        if s.verbose : s.logger.info("KnowledgeModeler removetaxonomy : taxonomy :" + s.domain)
        if s.domaincollection != None:
            s.maT.removeCollection( )
            s.maC.removeCollection( )
            s.maTfIdf.removeCollection()


    def addcorpus(s):
        global leafNode
        enc = 'utf-8'
        try:
            # here Schema is indetendto be a JSON file
            json_data = json.load(open(s.corpus, 'r', encoding=enc))
            key = json_data['corpora']

            for dom in key:
                corpus = str(dom['topic'])
                domain = str(dom['domain'])

                domain = domain.replace(' ', '_')
                if s.verbose: s.logger.info("addcorpus: domain :" + domain + ' corpus source :' + corpus)
                s.settaxonomy(domain)
                taxonomy = s.listtaxonomy()

                taxonomy = taxonomy['taxonomy']
                taxonomy = {"children": taxonomy}

                if s.verbose: s.logger.info("TAXONOMY : " + str(taxonomy))
                if (not domain):
                    if s.verbose: s.logger.info(
                        "addcorpus : FAIL taxonomy : " + str(domain) + " *NOT FOUND* . Can not add corpus")
                    return False
                if (not corpus):
                    s.logger.info("addcorpus : FAIL corpus key *NOT FOUND*. Can not add corpus")
                    return False

                s.setcorpus(corpus)
                if s.verbose: s.logger.info("addcorpus :taxonomy : " + s.domaincollection)
                s.maC = MongoAccessor(host=s.mongohost, port='27017', db='KnowledgeModelCorpora',
                                      collection=s.domaincollection
                                      , logger=s.logger)
                leafNode = ""
                node = s.locateByName(taxonomy, corpus)
                if s.verbose: s.logger.info("addcorpus : leafNode <" + str(leafNode) + "> node :" + str(node))
                if leafNode:
                    if s.verbose: s.logger.info("addcorpus :Upserting record for corpus :" + corpus)
                    s.maC.upsertRecord({"topic": str(corpus), "domain": domain}
                                       , {"body": dom['body'], "domain": domain, "topic": corpus}
                                       , upsert=True)

            return True
        except Exception as e:
            print(help_message)
            print(("** %s Exception** %s:") % (sys.argv[0], str(e)))
            return False

    def addtfidf(s):
        json_data = s.corpusweights()
        for key in json_data:
            if s.verbose : s.logger.info("Key :" + str(key['topic']))
            if s.verbose : s.logger.info("Upserting record for key :"+ key['topic'])
            s.maTfIdf.upsertRecord(
                    {"topic" : str(key['topic'])}
                    , {
                        "phrases" : key['phrases']
                        , "domain" : s.domaincollection
                        , "topic" : str(key['topic'])
                        , 'timestamp': strftime("%Y-%m-%d %H:%M:%S", gmtime())
                        }
                    ,  upsert=True )


    def corpusweights(s):

        records = s.maC.getRecords()
        tfidf = []
        topics = []
        corpus = []
        for record in records:
            if (record['domain'] == s.domain):
                topics.append(record['topic'])
                corpus.append(record['body'])
        if s.verbose : s.logger.info("corpusweights : topics : " + str(topics) + " len(corpus) : " + str(len(corpus)))

        tf = TfidfVectorizer(analyzer='word', ngram_range=(1,3), stop_words='english', lowercase=True, token_pattern='[A-Za-z]{2,}')
        tokenize = tf.build_tokenizer()
        tfidf_matrix = tf.fit_transform(corpus)
        feature_names = tf.get_feature_names()
        dense_tfidf_matrix = tfidf_matrix.todense()

        for i in range(0, len(dense_tfidf_matrix)):
            topic = dense_tfidf_matrix[i].tolist()[0]
            # filter out phrases with a score of 0
            phrase_scores = [pair for pair in zip(range(0, len(topic)), topic) if pair[1] > 0]
            sorted_phrase_scores = sorted(phrase_scores, key=lambda t: t[1] * -1)

            # find the min and max score for normalization by grabbing the scores of
            # the first and last elements in the sorted list
            max_score = sorted_phrase_scores[0][1]
            min_score = sorted_phrase_scores[len(sorted_phrase_scores) - 1][1]

            tfidf.append(dict({'topic': topics[i], 'phrases': []}))
            for phrase, score in [(feature_names[word_id], score) for (word_id, score) in sorted_phrase_scores]:
                # normalize scores to a 0 to 1 range
                normalized_score = (score - min_score) / (max_score - min_score)
                normalized_score = 1 - 100**(-1 * normalized_score)#(score - min_score) / (max_score - min_score)
                tfidf[i]['phrases'].append(dict({'phrase': phrase, 'score': normalized_score}))

        return tfidf

    def locateByName(s, e,name):
        global leafNode

        if s.verbose : s.logger.info("Locate by Name : name :" + str(name))

        if e.get('name',None) == name:
            # is this a leaf node or does it have children?
            #If children, then can not point to a corpus
            children = e.get('children', None)
            if children is None:
                leafNode = name
                return e
            else:
                leafNode = ""
                return e

        for child in e.get('children',[]):
            result = s.locateByName(child,name)
            if result is not None:
                return result
        return None
    def selfidentify(s):
        s.logger.info("Knowledge Modeler version :" + __version__)

def main(argv=None):
    mongohost = os.environ.get('MONGOHOST')
    if not mongohost:
        mongohost = 'mongo'
    taxonomysource = corpus = domain =  msg = None
    verbose = newtaxonomy = removetaxonomy = listflag = listTfIdfFlag = addcorpus = addtfidf = False
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
            opts, args = getopt.getopt(argv[1:], "hT:D:C:c:M:rnvlLat"
                    , ["help", "TaxonomySource=", "Domain=", "corpus=",  "MONGOHOST=", "removetaxonomy", "newtaxonomy", "verbose", "list", "List", "addcorpus", "tfidf"])
        except (getopt.error, msg):
            raise Usage(help_message)

        # option processing
        for option, value in opts:
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-T", "--TaxonomySource"):
                taxonomysource = value
            if option in ("-D", "--Domain"):
                domain = value
            if option in ("-c", "--corpus"):
                corpus = value
            if option in ("-M", "--MONGOHOST"):
                mongohost = value
            if option in ("-v", "--verbose"):
                verbose = True
            if option in ("-r", "--removetaxonomy"):
                removetaxonomy = True
            if option in ("-n", "--newtaxonomy"):
                newtaxonomy = True
            if option in ("-l", "--list"):
                listflag = True
            if option in ("-L", "--ListTfIdf"):
                listTfIdfFlag = True
            if option in ("-a", "--addcorpus"):
                addcorpus = True
            if option in ("-t", "--tfidf"):
                addtfidf = True

        if (removetaxonomy and domain is None):              raise DeleteTaxonomyUsage(remove_msg)
        if ( newtaxonomy   and taxonomysource is None):      raise NewTaxonomyUsage(new_msg)
        if ( addcorpus     and (not domain or not corpus) ): raise AddUsage(add_msg)
        if ( addtfidf      and (not domain) ):               raise AddTfIdfUsage(add_tfidf_msg)
        if ( listTfIdfFlag and not domain ):                 raise ListUsage(list_msg)
    except Usage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        print("Usage\n\t", help_message, file=sys.stderr)
        return 2
    except DeleteTaxonomyUsage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("Delete Usage\n\t", remove_msg, file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        return 2
    except NewTaxonomyUsage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("New Model Usage\n\t", new_msg, file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        return 2
    except AddUsage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("Add Usage\n\t", add_msg, file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        return 2
    except AddTfIdfUsage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("Add TfIdf Usage\n\t", add_tfidf_msg, file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        return 2
    except ListUsage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("List Usage\n\t", list_msg, file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        return 2
    except UpdateUsage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("Update Usage\n\t", add_msg, file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        return 2
    t = KnowledgeModel(
        taxonomysource=taxonomysource, corpus=corpus, domain=domain
        ,mongohost=mongohost
        ,remove_taxonomy=removetaxonomy, list_flag=listflag, list_tfidf_flag= listTfIdfFlag, new_taxonomy=newtaxonomy
        ,add_corpus=addcorpus, add_tfidf=addtfidf
        ,logger=logger, verbose=verbose)
    if t.remove_taxonomy:
        logger.info("Deleting Taxonomy = " + t.domain)
        t.removetaxonomy()
        return
    if t.new_taxonomy: #
        logger.info("Creating/Updating Taxonomy from corpus " + t.taxonomysource  )
        t.createtaxonomy()
        return
    if t.list_flag:
        if (t.domain):
            logger.info("Finding/Taxonomy = " + t.domain  )
            tx = t.listtaxonomy()
            logger.info("Taxonomy Records >>\n" + str(json.dumps(tx, indent=4, sort_keys=True)))
        else:
            tx = t.listalltaxonomies()
            logger.info("Taxonomy Records >>\n" + str(json.dumps(tx, indent=4, sort_keys=True)))

        if (t.corpus):
            if not t.domain:
                logger.info("Can't list corpus without a taxonomy specification")
            else:
                cx = t.listcorpus()
                logger.info("Corpus Records >>\n" + str(json.dumps(cx, indent=4, sort_keys=True)))
    if t.list_tfidf_flag:
        tfidfx = t.listtfidf()
        logger.info("TfIdf Records >>\n" + str(json.dumps(tfidfx, indent=4, sort_keys=True)))

    if t.add_corpus: #
        logger.info("Adding/Updating corpus = " + t.corpus  )
        tx = t.addcorpus()
        return
    if t.add_tfidf: #
        logger.info("Adding/Updating tdidf scores. domain = " + t.domain  )
        tx = t.addtfidf()
        return
if __name__ == "__main__":
    sys.exit(main())
