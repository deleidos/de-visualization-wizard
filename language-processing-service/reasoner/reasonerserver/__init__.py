from pyramid.config import Configurator
from pyramid.events import NewRequest

def add_cors_headers_response_callback(event):
    def cors_headers(request, response):
        response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST,GET,DELETE,PUT,OPTIONS',
        'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Max-Age': '1728000',
        })
    event.request.add_response_callback(cors_headers)

def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.add_subscriber(add_cors_headers_response_callback, NewRequest)

    config.add_settings({'MODELERLOCATION': settings['modelerlocation'] })

    config.add_route('questionanalysis', '/questionanalysis/{question}')
    config.add_route('topicmatching', '/topicmatching/{domain}')
    config.add_route('datasetranking', '/datasetranking/{domain}/{analytic_type}/{interpretation}')
    config.add_route('vizranking', '/vizranking')
# Knowledgemodel and domain models
    # config.add_route('getcorpus', '/getcorpus/{corpus}')
    # config.add_route('gettaxonomyfordomain', '/gettaxonomyfordomain/{domain}')
    # config.add_route('gettfidffordomainX', '/gettfidffordomain/{domain}/{corpus}')

    config.scan('.views')
    return config.make_wsgi_app()
