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

from .topicmatching.questionanalyzer import QuestionAnalyzer
from .topicmatching.topicmatcher import TopicMatcher
from .datamatching.datamatcher import DataMatcher

@view_config(permission='get', route_name='questionanalysis', renderer='json')
def question_analysis_service(request):
    question = request.matchdict.get('question')
    log.info('Running question analysis on "' + question + "'")
    qa = QuestionAnalyzer(question, request.registry.settings['MODELERLOCATION'], logger=log)

    question_data = {}

    tenses = qa.getTenses()
    ngrams = qa.getNgrams()
    whTerms = qa.getWhTerms()

    question_data['tagged'] = qa.tagged

    question_data['past'] = tenses[0]
    question_data['present'] = tenses[1]
    question_data['future'] = tenses[2]

    question_data['bigrams'] = ngrams[0]
    question_data['trigrams'] = ngrams[1]

    question_data['whTerms'] = whTerms

    question_data['lemmas'] = qa.getLemmas()

    question_data['analyticType'] = qa.getAnalyticType(tenses, whTerms)
    question_data['correctedWords'] = qa.correctSpelling()
    question_data.update(qa.getWhAnalysis())

    return question_data

@view_config(permission='get', route_name='topicmatching', renderer='json')
def topic_matching_service(request):
    parsed = urlparse(request.path_qs)
    question_words = parse_qsl(parsed.query)
    domain = request.matchdict.get('domain').replace(' ', '_')
    log.info('Topic matching on domain {}'.format(domain))

    tm = TopicMatcher(domain, request.registry.settings['MODELERLOCATION'], logger=log)
    data = tm.topic_matching(question_words)
    log.info('Topic matching completed')
    if not data:
        raise exc.HTTPInternalServerError(explanation="Topic matching failed. " +
                                          "A model has not been generated for the given taxonomy.")
    return data

@view_config(permission='get', route_name='datasetranking', renderer='json')
def data_set_ranking_service(request):
    domain = request.matchdict.get('domain')
    analytic_type = request.matchdict.get('analytic_type')
    interpretation = request.matchdict.get('interpretation')
    log.info('Ranking data sets with\ndomain: {}\nanalytic type: {}\ninterpretation: {}'.format(domain, analytic_type, interpretation))

    dm = DataMatcher(request.registry.settings['MODELERLOCATION'])
    ranking = dm.dataSetRanking(domain, analytic_type, interpretation)
    log.info('Data set ranking completed')
    log.info(ranking)
    if not ranking:
        raise exc.HTTPInternalServerError(explanation="There were no data sets found in the database.")
    return ranking

@view_config(permission='get', route_name='vizranking', renderer='json')
def viz_ranking_service(request):
    log.info('Ranking vizes')
    parsed = urlparse(request.path_qs)
    question_analysis = parse_qs(parsed.query)

    dm = DataMatcher(request.registry.settings['MODELERLOCATION'])
    ranking = dm.vizRanking(question_analysis)
    log.info('Viz ranking completed')
    log.info(ranking)
    if not ranking[0]['viz_ranks']:
        raise exc.HTTPInternalServerError(explanation="There were no visualizations found in the database.")
    return ranking
