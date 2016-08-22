from pyramid.config import Configurator
from pyramid.events import NewRequest
import os

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
    MONGOHOST = None
    try:
        MONGOHOST = os.environ['MONGOHOST']
        config.add_settings({'MONGOHOST': MONGOHOST} )
    except KeyError as e:
        print ("Can not find enviromnetal variable 'MONGOHOST'. Error : " + str(e) )
        config.add_settings({'MONGOHOST': settings['mongohost'] })

    sttgs = config.get_settings()
    print ("MONGO HOST : " , sttgs['MONGOHOST'] )
    config.add_subscriber(add_cors_headers_response_callback, NewRequest)

# Knowledgemodel and domain models
    config.add_route('getcorpus',            '/getcorpus/{corpus}')
    config.add_route('gettaxonomyfordomain', '/gettaxonomyfordomain/{domain}')
    config.add_route('gettfidffordomain',    '/gettfidffordomain/{domain}/{corpus}')
    config.add_route('gettfidfs',            '/gettfidfs/{domain}')
    config.add_route('getschema',            '/getschema/{sid}')
    config.add_route('getschemas',           '/getschemas')
    config.add_route('getencodings',         '/getencodings')
    config.add_route('getarchetypes',        '/getarchetypes')
    config.add_route('getdatasets',          '/getdatasets')
    config.add_route('getvisualizations',    '/getvisualizations')
    config.add_route('getdomains',           '/getdomains')
    config.add_route('getinterpretations',   '/getinterpretations')
    config.add_route('getspellcheckcorpus',  '/getspellcheckcorpus')
    config.add_route('getquestionterms',     '/getquestionterms')
    config.add_route('getschemadescription', '/getschemadescription/{sid}')
    config.add_route('getvisualization',     '/getvisualization/{visualizationame}')
    config.add_route('processmodel',         '/processmodel/{domain}/{terms}')
    config.scan('.views')
    return config.make_wsgi_app()
