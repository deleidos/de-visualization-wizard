__copyright__ = "Copyright 2016, Leidos, Inc."
__license__ = "Apache 2.0"
__status__ = "Beta"
__year__ = "2016"

# package
from pyramid.response import Response
from pyramid.view import view_config
from pyramid.config import Configurator
import pyramid.httpexceptions as exc
import os.path
import os
import sys, ast, getopt
import logging
log = logging.getLogger(__name__)

from urllib.parse import urlparse, parse_qsl, parse_qs

# domain and knowledge modeler package
# from knowledgemodeler.knowledgemodeler import KnowledgeModel as DM
# from domainmodeler import Trainer as DM
from modelerserver.mongoaccessor.mongoaccessor import MongoAccessor as MA
from modelerserver.mongoaccessor.mongoaccessor import GridFSModel
#from modelerserver.domainmodeler.word2vec.w2vmodel import W2VModels as M
from .domainmodeler.word2vec.w2vmodel import W2VModels as M

# logger needed for Mongo accessor
program = os.path.basename(sys.argv[0])
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
logging.root.setLevel(level=logging.INFO)
logger = logging.getLogger(program)


@view_config(permission='get', route_name='getcorpus', renderer='json')
def getcorpus(request):
    mongohost = request.registry.settings['MONGOHOST']
    corpus = request.matchdict.get('corpus')
    log.info('Getting Corpus : getcorpus:' + corpus )
    ma = MA(host=mongohost, port=27017, logger=logger, db='KnowledgeModelCorpora', collection='corpora')
    record = ma.getRecord({"corpus" : corpus})
    return record
@view_config(permission='get', route_name='gettaxonomyfordomain', renderer='json')
def gettaxonomy_for_domain(request):
    mongohost = request.registry.settings['MONGOHOST']
    domain = request.matchdict.get('domain')
    log.info('Getting Taxonomy for Domain : domain:' + domain )
    ma = MA(host=mongohost, port=27017, logger=logger, db='KnowledgeModelTaxonomy', collection=domain.replace(' ', '_'))
    record = ma.getRecord({"domain" : domain})
    if record is None:
        raise exc.HTTPBadRequest(explanation="The domain {} does not have a taxonomy in the database.".format(domain))

    return record

@view_config(permission='get', route_name='gettfidffordomain', renderer='json')
def gettfidf_for_domain(request):
    mongohost = request.registry.settings['MONGOHOST']
    domain = request.matchdict.get('domain')
    corpus = request.matchdict.get('corpus')
    log.info('Getting TF-IDF for Domain : domain:' + domain + " corpus :" + corpus )
    ma = MA(host=mongohost, port=27017, logger=logger, db='KnowledgeModelTfIdf', collection='tfidf')
    record = ma.getRecord({"domain" : domain, "corpus" : corpus})
    return record

@view_config(permission='get', route_name='gettfidfs', renderer='json')
def gettfidfs(request):
    mongohost = request.registry.settings['MONGOHOST']
    domain = request.matchdict.get('domain').replace(' ', '_')
    log.info('Getting all TF-Idf results for domain {}'.format(domain))
    ma = MA(host=mongohost, port=27017, logger=logger, db='KnowledgeModelTfIdf', collection=domain)
    return (ma.getRecords())

@view_config(permission='get', route_name='getschema', renderer='json')
def getschema(request):
    mongohost = request.registry.settings['MONGOHOST']
    sId = request.matchdict.get('sid')
    log.info('Getting Schema for ID : ' + sId )
    ma = MA(host=mongohost, port=27017, logger=logger, db='vizwiz', collection='Schemas')
    record = ma.getRecord({"sId": sId} )
    return record

@view_config(permission='get', route_name='getschemas', renderer='json')
def getschemas(request):
    mongohost = request.registry.settings['MONGOHOST']
    log.info('Getting all Schemas for ID')
    ma = MA(host=mongohost, port=27017, logger=logger, db='vizwiz', collection='Schemas')
    record = ma.getRecords()
    return record

@view_config(permission='get', route_name='getencodings', renderer='json')
def getencodings(request):
    mongohost = request.registry.settings['MONGOHOST']
    log.info('Getting all Encodings for ID')
    ma = MA(host=mongohost, port=27017, logger=logger, db='vizwiz', collection='Encodings')
    record = ma.getRecords()
    return record

@view_config(permission='get', route_name='getarchetypes', renderer='json')
def getarchetypes(request):
    mongohost = request.registry.settings['MONGOHOST']
    log.info('Getting all Archetypes for ID')
    ma = MA(host=mongohost, port=27017, logger=logger, db='vizwiz', collection='Archetypes')
    record = ma.getRecords()
    return record

@view_config(permission='get', route_name='getdatasets', renderer='json')
def getdatasets(request):
    mongohost = request.registry.settings['MONGOHOST']
    log.info('Getting all DataSets for ID')
    ma = MA(host=mongohost, port=27017, logger=logger, db='vizwiz', collection='DataSets')
    record = ma.getRecords()
    return record

@view_config(permission='get', route_name='gettfidfs', renderer='json')
def getinterpretations(request):
    mongohost = request.registry.settings['MONGOHOST']
    log.info('Getting all TF-Idf results')
    ma = MA(host=mongohost, port=27017, logger=logger, db='KnowledgeModelTfIdf', collection='tfidf')
    return (ma.getRecords())

@view_config(permission='get', route_name='getvisualizations', renderer='json')
def getvisualizations(request):
    mongohost = request.registry.settings['MONGOHOST']
    log.info('Getting all Visualizations for ID')
    ma = MA(host=mongohost, port=27017, logger=logger, db='vizwiz', collection='Visualizations')
    record = ma.getRecords()
    return record

@view_config(permission='get', route_name='getdomains', renderer='json')
def getdomains(request):
    mongohost = request.registry.settings['MONGOHOST']
    log.info('Getting all Visualizations for ID')
    ma = MA(host=mongohost, port=27017, logger=logger, db='vizwiz', collection='Domains')
    record = ma.getRecords()
    return record

@view_config(permission='get', route_name='getinterpretations', renderer='json')
def getinterpretations(request):
    mongohost = request.registry.settings['MONGOHOST']
    log.info('Getting all Visualizations for ID')
    ma = MA(host=mongohost, port=27017, logger=logger, db='vizwiz', collection='Interpretations')
    record = ma.getRecords()
    return record

@view_config(permission='get', route_name='getschemadescription', renderer='json')
def getschemadescription(request):
    mongohost = request.registry.settings['MONGOHOST']
    sId = request.matchdict.get('sid')
    log.info('Getting Schema Description for ID : ' + sId )
    ma = MA(host=mongohost, port=27017, logger=logger, db='SchemasData', collection='schemadescriptions')
    record = ma.getRecord({"sId": sId} )
    return record

@view_config(permission='get', route_name='getspellcheckcorpus', renderer='json')
def getspellcheckcorpus(request):
    mongohost = request.registry.settings['MONGOHOST']
    log.info('Getting spell check corpus')
    ma = MA(host=mongohost, port=27017, logger=logger, db='vizwiz', collection='Spelling')
    record = ma.getRecords()
    return record

@view_config(permission='get', route_name='getquestionterms', renderer='json')
def getquestionterms(request):
    mongohost = request.registry.settings['MONGOHOST']
    log.info('Getting pos terms')
    ma = MA(host=mongohost, port=27017, logger=logger, db='vizwiz', collection='Dictionary')
    record = ma.getRecords()
    return record

@view_config(permission='get', route_name='getvisualization', renderer='json')
def getvisualization(request):
    mongohost = request.registry.settings['MONGOHOST']
    visualizationame = request.matchdict.get('visualizationame')
    log.info('Getting Visualisation for name : ' + visualizationame  + " mongo host : " + mongohost)
    ma = MA(host=mongohost, port=27017, logger=logger, db='vizwiz', collection='Visualizations')
    record = ma.getRecord({"name": visualizationame} )
    return record

# tells the w2vmodel class to change the loaded model
@view_config(permission='get', route_name='processmodel', renderer='json')
def process_model(request):
    mongohost = request.registry.settings['MONGOHOST']
    domain = request.matchdict.get('domain').replace(' ', '_')
    modelName = domain + '_mdl'
    gfsm = GridFSModel(modelName=modelName, host=mongohost, port=27017, logger=logger)
    model = gfsm.getModelFromGridFS()
    if model is None:
        raise exc.HTTPBadRequest(explanation="The domain {} does not have a domain model loaded.".format(domain))

    w2vmodel = M(modelName=modelName, model=model, logger=logger, verbose=True)
    log.info("Created W2VModel:" + modelName)

    terms = request.matchdict.get('terms', -1)
    w2vmodel.setTerms(terms)
    most_similar_terms = w2vmodel.process()
    log.info("Processing Terms :" + str(w2vmodel.getTerms()))
    return most_similar_terms
