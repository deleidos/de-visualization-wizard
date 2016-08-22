#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__copyright__ = "Copyright 2016, Leidos, Inc."
__license__ = "Apache 2.0"
__status__ = "Beta"
__year__ = "2016"

description = '''
Domains are used to categorize all of the data and visual tools into a specific environment.
Domains are a concept derived from the Schema Wizard tool. Although the domain names can be anything,
the best domains names are high-level categories that encompass a certain segment or concept.
'''

# standard imports
import logging
import os.path
import os
import sys, ast, getopt
import multiprocessing
import PyPDF2
import json
import configparser
config = configparser.ConfigParser()
from time import gmtime, strftime

# other libraries
#from gensim.corpora import WikiCorpus
from gensim.models import Word2Vec
from gensim.models.word2vec import LineSentence
# local imports in this package
from news_corpus_builder import NewsCorpusGenerator
from modelerserver.mongoaccessor.mongoaccessor import MongoAccessor , GridFSModel

# some global variable
help_message = ('''
****************************************************************************************************
* %s                                                                                 *
* Add Domain    python domainmodeler.py -n -D "<domain name>"                                      *
* Add Domains   python domainmodeler.py -n -d "<path to domain name JSON file>"                    *
* Add Domain w/ Docs    python domainmodeler.py -a -f                                              *
*                "<path to domain corpus text file>" -D "<domain name>"                            *
* Add Domain w/ Websites python domainmodeler.py -a -t                                             *
*                "<path to .ini file>" -D "<domain name>"                                          *
* Update Domain Titles  python domainmodeler.py -R -D "<old domain>:<new domain>"                  *
* List Domains  python domainmodeler.py -l -D "<domain name>"                                      *
* Delete Domain python domainmodeler.py -r -D "<domain name>"                                      *
****************************************************************************************************

'''
%
    (sys.argv[0])
)
remove_msg = ('''
%s requires a model specification
''' % (sys.argv[0]))
new_msg = ('''
%s requires a model specification
''' % (sys.argv[0]))

add_msg = ('''
%s requires a topics ini file to crawl
''' % (sys.argv[0]))

update_msg = ('''
%s requires a model specification AND Model must exist
''' % (sys.argv[0]))

g_model_extension = '_mdl'

class Usage (Exception):
  def __init__(s, value):
    s.value = value
  def __str__(s):
    return repr(s.value)

class DeleteModelUsage (Exception):
  def __init__(s, value):
    s.value = value
  def __str__(s):
    return repr(s.value)
class NewModelUsage (Exception):
  def __init__(s, value):
    s.value = value
  def __str__(s):
    return repr(s.value)
class AddUsage (Exception):
  def __init__(s, value):
    s.value = value
  def __str__(s):
    return repr(s.value)

class UpdateUsage (Exception):
  def __init__(s, value):
    s.value = value
  def __str__(s):
    return repr(s.value)

class DomainModeler  (object):
    def __init__(s,topicsfile=None, pdfSource=None, textfile=None
                 , mongohost='localhost'
                 , domainsourcefile =None
                 , domain= None
                 , modelStore=None, modelName ='', word2vecflag=None
                 , removeFlag =False, renameflag=False , newFlag=False
                 , listFlag = False, addFlag=False
                 , logger=None, verbose=False):
        s.topicsfile = topicsfile
        s.textfile = textfile
        s.removeFlag = removeFlag
        s.renameflag = renameflag
        s.newFlag = newFlag
        s.listFlag = listFlag
        s.addFlag=addFlag
        s.pdfSource = pdfSource
        s.mongohost = mongohost
        s.domainsourcefile  = domainsourcefile
        s.domain = domain
        s.collectionname = ''

        # note the domain may have embedded spaces. These get replaced by the '_' character.
        if (s.domain is not None): s.collectionname = s.domain.replace(' ' , '_')
        else: s.collectionname = 'articles'
        if (s.domain is not None):
            s.domain_external_name = s.domain.replace(' ' , '_')
        else:
            s.domain_external_name = ''

        s.modelStore = modelStore
        s.modelName = s.internal2external(s.domain)
        s.corpus_dir = 'NewsCorpus'
        # s.article_links = []
        s.domain_total = 300

        s.word2vecflag = word2vecflag
        s.topics = []
        s.logger = logger
        s.verbose = verbose
        if s.topicsfile:
            retval = s.readConfigFromIniFile()
            if not retval: sys.exit(-1)
        if s.verbose : s.logger.info("__init__ : domain :" + str(s.domain) + " external model :" + str(s.domain_external_name))
        # mongo instances
        s.maD = MongoAccessor(host=mongohost, port='27017', db='vizwiz', collection='Domains', logger=s.logger)
        s.maC = MongoAccessor(host=mongohost, port='27017', db='DomainModelCorpora', collection=s.collectionname, logger=s.logger)
        # gridFs instance
        s.setModelName()
        s.gfs = GridFSModel(modelName=s.modelName, host=mongohost, port='27017', logger=s.logger)
        # does the <domain>_mdl already exist?
        s.existingModel = s.getDomainModel()
        if s.verbose : s.logger.info("Existing Model in Mongo==>" + str(s.existingModel))
        s.lineSentence = None
        s.sentences = []

        if s.domain : s.ncg = NewsCorpusGenerator(s.corpus_dir, 'mongo', mongo_db_name='DomainModelCorpora', domain=s.domain)

    def crawl_links(s, terms, domain):
        s.domain_articles = []
        if s.verbose : s.logger.info("crawl_links  # s.domain_total >> " + str(s.domain_total) + " terms :" + str(( terms)) )
        article_count = int(s.domain_total / len(terms))
        for term in terms:
            s.domain_articles.extend(s.ncg.google_news_search(term, domain, article_count))
        return s.domain_articles

    def readDomainTopics(s):
        s.topics = []
        lines = []
        try:
            with open (s.topicsfile, 'r') as f:
                lines = f.readlines()
            for line in lines:
                    line = line.strip()
                    line = line.split(',')
                    for words in line:
                        words = words.split()
                        words = ' '.join(words)
                        if s.verbose : s.logger.info("readDomainTopics  : words >> " + str(words))
                        s.topics.append(words)
        except Exception as e:
            print (help_message)
            print(("** %s Exception** %s:") % (sys.argv[0], str(e)) )
            return False

    def external2internal(s):
        s.domain = (s.domain_external_name.replace('_mdl' , ''), None)[s.domain_external_name is None]
        s.domain = (s.domain.replace('_' , ''), None)[s.domain is None]
    def internal2external(s, domain):
        if (domain is not None):
            domain_external_name = (domain.replace(' ', '_'), None)[domain is None]
            domain_external_name = domain_external_name + '_mdl'
        else:
            domain_external_name = ''
        return domain_external_name

    def setSentences(s, sentences):
        s.sentences. append (sentences)

    def setDomain(s, domain):
        s.domain = domain
    def getDomainByName(s):
        return s.maD.getRecord({"domain": s.domain})

    def getDomainByDomain(s):
        return s.maD.getRecord({"domain": s.domain})

    def readConfigFromIniFile(s):

        try:
            config.read(s.topicsfile)
            if s.verbose : s.logger.info("config.sections==>" + str(config.sections()) )

            domain = config['domain']
            if (s.domain is None) : s.domain = domain['domain']

            if s.verbose : s.logger.info("Domain ==> " + str(s.domain) )

            modelName = config['model name']
            s.modelName = (s.modelName,modelName['model name'] )[s.modelName is None]
            s.modelName = s.setModelName()
            if s.verbose : s.logger.info("Model Name ==> " + str(s.modelName) )

            terms = config['terms']
            terms = terms['terms'].strip()
            if s.verbose : s.logger.info("Terms ==>\n" +  terms + '\n')

            termsLines = terms.split('\n')

            for multipleterms in termsLines:
                termsTuple = multipleterms.split(',')
                correctedList = []
                for item in termsTuple:
                    item = ' '.join(item.split())
                    if item != '':
                        correctedList.append(item)
                if (len(correctedList) >0):  s.topics.append(correctedList)
            return True
        except Exception as e:
            print (help_message)
            print(("** %s Exception** %s:") % (sys.argv[0], str(e)) )
            return False

    def removeDomainModel(s):
        #
        if s.modelStore != None:
            # remove from GridFS
            if s.verbose : s.logger.info (str(s.modelName))
            s.gfs.dropModelFromGridFS(s.modelName)

            if os.path.exists(s.modelStore):
                # remove from file system
                os.remove(s.modelStore)
    def removeDomain(s):
        # remove the domain record
        if s.verbose : s.logger.info("remove Domain : " + str(s.domain))
        s.maD.deleteRecord({"domain": s.domain})
        # remove the <domain>_mdl GridFS DB
        if s.verbose : s.logger.info ("remove Domain Model : " + str(s.modelName))
        s.gfs.dropModelFromGridFS(s.modelName)
        # remove the DomainCorpora collection for the domain
        if s.verbose : s.logger.info("remove DomainModelCorpora : " + str(s.maC))
        s.maC.removeCollection()

    def renameDomain(s, newdomain):
        newdomain_external = s.internal2external(newdomain)
        newcollection = newdomain.replace(' ', '_')
        s.logger.info("renameDomain : newdomain : " + newdomain + " newcollection :" + newcollection + ' newdomain_external : ' + newdomain_external)
        # (1). update the domain record
        s.maD.upsertRecord({"domain": s.domain}
            , {"domain": newdomain}
            , upsert=True)
        # (2). db.collection.renameCollection("new_collection_name")
        s.maC.renameCollection(newcollection)
        # (3). a. read in the <original_domain>_mdl to memory.
        s.model = s.gfs.getModelFromGridFS()
        # (3). b. save the memory resident model to GridFs  <new_domain>_mdl
        s.modelName = newdomain_external
        s.setModelName()
        s.gfs.setModelName(s.modelName)
        s.gfs.saveModelToGridFS(s.model)

    def getDomainModel(s):
        ma = MongoAccessor(host=s.mongohost, port='27017', db="", collection="", logger=s.logger)
        c = s.domain_external_name + g_model_extension
        allModels = list(ma.client.database_names())
        if (c in allModels): return True
        else: return False

    def listDomain(s):
        ma = MongoAccessor(host=s.mongohost, port='27017', db= "", collection="",  logger=s.logger)
        allModels = list (ma.client.database_names())
        if (s.domain is not None):
            record = s.maD.getRecord({"Domain": s.domain})
            if s.verbose : s.logger.info("Domain record : " + str(record))

            c= s.domain_external_name + g_model_extension
            if (c in allModels):
                if s.verbose : s.logger.info ("Domain Model : " +  str(c) )
            if s.verbose : s.logger.info ("Domain Model Corpora Record Count: " +str( s.maC.getRecordCountForQuery({"domain": s.domain})) )
            return record

        else:
            models = [ ]
            records = s.maD.getRecords()
            for c in allModels :
                if g_model_extension in c and c not in models: models.append(c)
            if s.verbose : s.logger.info ("All Models : " +  str(models) )
            return records


    def createDomainFromString(s):
        s.logger.info("createDomainFromString: domain : " + s.domain)
        # get corresponding dataset
        s.maD.upsertRecord({"domain": s.domain}
                           , {"domain": s.domain}
                           , upsert=True)
        return True

    def createDomainfromFile(s):
        enc = 'utf-8'
        try:
            json_data = json.load(open(s.domainsourcefile, 'r', encoding=enc))
            if s.verbose : s.logger.info("type(d) :" + str(type(json_data)) )

            if s.verbose : s.logger.info("createDomainFromFile JSON_data (dict) <json_data>:" + str(json_data))
            key = json_data['domains']

            if s.verbose : s.logger.info("Key Value:" + str(key))
            for dom in key:
                if s.verbose : s.logger.info("Upserting schema for domain :" + str(dom['domain']))
                s.setDomain(str(dom['domain']))
                s.maD.upsertRecord({"domain": str(dom['domain']) }
                                   , {"domain": str(dom['domain']) }
                                   , upsert=True)
            return True
        except Exception as e:
            print (help_message)
            print(("** %s Exception** %s:") % (sys.argv[0], str(e)) )
            return False

    def trainModelFromTopics(s):
        if s.verbose : s.logger.info ("trainModelFromTopics : Topics :" +  str(s.topics) )
        ncg = NewsCorpusGenerator(s.corpus_dir, 'mongo', mongo_db_name='DomainModelCorpora', domain=s.domain)

        article_links = []
        for t in s.topics:
            # Extract Content & Create Corpus
            article_links.extend( s.crawl_links( t, s.domain) )
        # 1. crawl the topics
        if s.verbose : s.logger.info ( ("Total %d links to extract" % len(article_links) )  + " links ==>" + str( article_links ) )
        # 2. store results in mongoDB
        ncg.generate_corpus(article_links)
        if s.verbose : s.logger.info  ("trainModelFromTopics : Stats:" + str( ncg.get_stats() ) )


    def setSentences(s, sentences):
        s.sentences. append (sentences)
        if s.verbose : s.logger.info ("Sentences : " + str(sentences) )

    def setModelName(s):
        if s.modelName is None:
            s.modelName = s.domain_external_name
        if s.verbose : s.logger.info("domainmodeler.setModelName(): s.modelName :" + s.modelName)
    def loadModelFromFileSystem(s):
        s.logger.info("domainmodeler.setModelName(): s.modelStore :" + str(s.modelStore) )
        return Word2Vec.load(s.modelStore)


    def W2V(s):
        s.maC.setDomain(s.domain)
        # grab the articles from Mongo
        rcount = s.maC.cacheArticles()
        if s.verbose : s.logger.info("Number of articles for domain:" + str(s.maC.getDomain()) + "==>" + str(rcount))
        for article in s.maC.cache:
            sentences = article['body'].split('\n')
            sentences[:] = (value for value in sentences if value != '')
            for sent in sentences:
                sentwords = sent.split()
                s.setSentences(sentwords)
        if s.verbose : s.logger.info("Number of sentences >> " + str(len(s.sentences))
                + " sentence[0] >>" + str(s.sentences[0]))
        # load model from mongo (gridfs)
        try:
            s.trainModelFromMongoDB()
        except Exception as e:
            print (help_message)
            print(("** %s Exception** %s:") % (sys.argv[0], str(e)) )
            return False


    def trainModelFromMongoDB(s):
        # Note full set of parameters @ http: // radimrehurek.com / gensim / models / word2vec.html  # gensim.models.word2vec.Word2Vec
        if s.existingModel :
            if s.verbose : s.logger.info("trainModelFromMongoDB: existingModel : " + s.modelName + ". . . ")
            s.model =  s.gfs.getModelFromGridFS()
            if s.verbose: s.logger.info("trainModelFromMongoDB : upsert : s.model:" + str(s.model))

            # s.model = s.loadModelFromFileSystem()
            s.model.train(s. sentences )
            if s.verbose : s.logger.info("trainModelFromMongoDB: existingModel : " + s.modelName + ". . . done")
        else:
            if s.verbose : s.logger.info("trainModelFromMongoDB: newFlag ... modelName : " + s.modelName)
            s.model = Word2Vec(
                s. sentences ,
                window=7, # maximum distance between the current and predicted word within a sentence.
                size=100, # is the dimensionality of the feature vectors
                min_count=10, # min # occurences: word appearing 1X/2X in a 1Bword corpus 1) uninteresting 2) typo 3) garbage
                workers=multiprocessing.cpu_count()
        )
        s.model.init_sims(replace=True)
        s.saveModelToFileSystem()
        s.setModelName()
        s.gfs.setModelName(s.modelName)
        s.gfs.saveModelToGridFS(s.model)
        s.maD.upsertRecord({"domain": s.domain}
            , {"domain": s.domain}
            , upsert=True)
        return s.model

    def trainModelFromText(s):
        # open the textfile and read eache text file there
        sentences = []
        with open (s.textfile, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip('\n')
            sentences.append( line.encode('latin-1', errors='ignore').decode('utf-8', errors='replace') )
        # cleanup and store in DomainModelCorpora
        clean_sentences = ''
        for sentence in sentences: clean_sentences += sentence + '\n'
        titlewords = sentences[0].split()
        title = ''
        if len(titlewords) > 10:title = ' '.join(titlewords[0:10])
        else: title = sentences[0]
        if s.verbose : s.logger.info("trainModelFromText : upsert : s.maC :" + str(s.maC))
        s.maC.upsertRecord(
                {"domain": s.domain, "title" :title}
                , {
                    'title': title
                    , 'domain' : s.domain
                    , 'body' : clean_sentences
                    , 'timestamp': strftime("%Y-%m-%d %H:%M:%S", gmtime())
                 }
                , upsert=True

        )

    def trainModelFromPDFText(s):
        sentences = []
        enc = 'utf-8'
        try:
            # Load PDF into pyPDF
            inF = open(s.pdfSource, "rb")
            pdf = PyPDF2.PdfFileReader(inF)
            # Iterate pages
            for i in range(0, pdf.getNumPages()):
                # Extract text from page and add to content
                line = pdf.getPage(i).extractText().strip()
                sentences.append(line.encode('latin-1', errors='ignore').decode('utf-8', errors='replace'))

            clean_sentences = ''
            for sentence in sentences:
                sent = sentence.strip()
                sent = sent.replace('.', '')
                clean_sentences += sent
            # remove punctuation
            titlewords = sentences[0].split()
            title = ''
            if len(titlewords) > 10:
                title = ' '.join(titlewords[0:10])
            else:
                title = sentences[0]
            if s.verbose: s.logger.info("trainModelFromPDFText : upsert : TITLE  :" + str(title))
            if s.verbose: s.logger.info("trainModelFromPDFText : upsert : SENT :" + str(clean_sentences))
            s.maC.upsertRecord(
                {"domain": s.domain, "title": title}
                , {
                    'title': title
                    , 'domain': s.domain
                    , 'body': clean_sentences
                    , 'timestamp': strftime("%Y-%m-%d %H:%M:%S", gmtime())
                }
                , upsert=True

            )
            return True
        except Exception as e:
            print(help_message)
            print(("** %s Exception** %s:") % (sys.argv[0], str(e)))
            return False

    def saveModelToFileSystem(s):
        if s.modelStore != None and s.modelName != None :
            if s.verbose : s.logger.info("saveModelToFileSystem : s.modelStore ==>" + s.modelStore)
            s.model.save(s.modelStore)
            return True
        else:
            s.logger.info("Failed to save to file system. modelStore ==> " + str( s.modelStore) + " model Name ==>" + str(s.modelName) )

    def selfIdentify(s):
        s.logger.info("DomainModeler  version :" + __version__)

def main(argv=None):
    mongohost = os.environ.get('MONGOHOST')
    if not mongohost:
        mongohost = 'mongo'

    domain = newdomain = domainsourcefile = pdfsource  = topicsfile = textfile = modelStore =word2vecflag = msg = None
    verbose = addFlag = removeFlag  = renameflag = newFlag = listFlag = False
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
            # opts, args = getopt.getopt(argv[1:], "hdaut:p:m:w:v", ["help", "remove", "add", "update", "topics=", "pdf=", "model=", "word2vecmodel=", "folder=", "verbose"])
            opts, args = getopt.getopt(argv[1:], "hrRnwaD:d:t:s:p:m:M:f:vl"
                    , ["help", "remove", "Rename","new", "word2vec", "add", "Domain=", "domainsourcefile=", "topics=", "source="
                    , "pdf=",  "model=", "MONGOHOST=", "file=", "verbose", "list"])
        except (getopt.error, msg):
            raise Usage(help_message)

        # option processing
        for option, value in opts:
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-r", "--remove"):
                removeFlag = True
            if option in ("-R", "--Rename"):
                renameflag = True
            if option in ("-n", "--new"):
                newFlag = True
            if option in ("-a", "--add"):
                addFlag = True
            if option in ("-t", "--topics"):
                topicsfile = value
            if option in ("-D", "--Domain"):
                domain = value
            if option in ("-d", "--domainsourcefile "):
                domainsourcefile  = value
            if option in ("-s", "--sources"):
                sourcesFolder = value
            if option in ("-m", "--model"):
                modelStore = value
            if option in ("-M", "--MONGOHOST"):
                mongohost = value
            if option in ("-w", "--word2vec"):
                word2vecflag = True
            if option in ("-p", "--pdf"):
                pdfsource = value
            if option in ("-f", "--file"):
                textfile = value
            if option in ("-v", "--verbose"):
                verbose = True
            if option in ("-l", "--list"):
                listFlag = True

        if (removeFlag  and domain is None): raise DeleteModelUsage(remove_msg)
        if (renameflag  and domain is None): raise DeleteModelUsage(remove_msg)
        if renameflag:
            domains = domain.split(':')
            if len(domains) == 1:
                raise DeleteModelUsage(remove_msg)
            else:
                domain = domains[0].strip()
                newdomain = domains[1].strip()
                logger.info("Renaming Domain ==> " + domain + "t ==> " + newdomain)

        if (word2vecflag  and domain is None): raise NewModelUsage(new_msg)
        if (newFlag and (domainsourcefile is None and domain is None) ):  raise NewModelUsage(remove_msg)
        if (addFlag):
            if (domain is None): raise AddUsage(add_msg)
            if (topicsfile is None and textfile is None and pdfsource is None):  raise AddUsage(add_msg)
    except Usage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        print("Usage\n\t", help_message, file=sys.stderr)
        return 2
    except DeleteModelUsage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("Delete Usage\n\t", remove_msg, file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        return 2
    except NewModelUsage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("New Model Usage\n\t", new_msg, file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        return 2
    except AddUsage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("Add Usage\n\t", add_msg, file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        return 2
    except UpdateUsage as e:
        print(sys.argv[0].split("/")[-1] + ": ", file=sys.stderr)
        print("Update Usage\n\t", add_msg, file=sys.stderr)
        print("Description\n\t", description, file=sys.stderr)
        return 2
    if verbose: logger.info("modelStore = " + str( modelStore) )
    t = DomainModeler (topicsfile=topicsfile, pdfSource = pdfsource, textfile=textfile
                    ,mongohost=mongohost
                    ,domainsourcefile =domainsourcefile
                    ,domain=domain
                    ,modelStore=modelStore, word2vecflag=word2vecflag
                    ,removeFlag=removeFlag ,renameflag=renameflag , newFlag=newFlag, addFlag=addFlag
                    ,listFlag = listFlag
                    ,logger=logger, verbose=verbose)
    if t.removeFlag :
        logger.info("Deleting Domain = " + t.domain )
        t.removeDomain()
    if t.renameflag:
        logger.info("Renaming Domain ==> " + t.domain + "t ==> " + newdomain)
        t.renameDomain(newdomain)
    if t.listFlag:
        tx = t.listDomain()
        logger.info("Domain Records >>\n" + str(json.dumps(tx, indent=4, sort_keys=True)))

        return
    if t.newFlag: # note requiement to name a model is already satisfied by above checks
        # entry condition: domainmodelr.py -n -m
        if t.domain:
            t.createDomainFromString()
        if t.domainsourcefile:
            t.createDomainfromFile()
        return
    if t.word2vecflag:
        t.W2V()
        return
    if (t.addFlag):
        if t.topicsfile is not None:
            logger.info("Crawling topics from ini = " + t.topicsfile)
            t.trainModelFromTopics()
        if t.textfile is not None:
            logger.info("Adding Text file  = " + t.textfile)
            t.trainModelFromText()
        if t.pdfSource is not None:
            logger.info("Using  pdf text source = " + t.pdfSource)
            t.trainModelFromPDFText()

if __name__ == "__main__":
    sys.exit(main())
