from flask import Flask
import engine.engine as engine
import sel.core as core
from SPARQLWrapper import SPARQLWrapper, JSON
import json

app = Flask(__name__)

@app.route('/getResults')
def findResults():

    return 'H'


def generate_json(query):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    engined = engine.Engine()
    types = engined.run(query)
    #matrix = generate_matrix(query)
    #matrix = [[[1],[0.4],[0.3],[0.6]],[[0.3],[1],[0.1],[0.5]],[[0.2],[0.4],[1],[0.6]],[[0.7],[0.3],[0.1],[1]]]
    #matrix = core.generate_matrix(dictUrlUri)
    #parse query
    #parsed_query = json.loads(query)
    parsed_query = query['Websites']
    dictType = dict()
    evaluateType(dictType,parsed_query)

    
    
            
    to_return =  json.dumps(data_json)
    return to_return
def alimentByType(parsed_query):
    for url in parsed_query:
        uris = url['URIs']['concepts']
        for uri in uris:
            name = uri
            uri = dict()
            uri['name'] = name
            uri['types'] = list()
            for type in core.obtain_types(uri):
                uri['type'].append(type)
        uris = url['URIs']['entitiesDisambiguated']
        for uri in uris:
            name = uri
            uri = dict()
            uri['name'] = name
            uri['types'] = list()
            for type in core.obtain_types(uri):
                uri.append(type)



def evaluateType(dictType,parsed_query):
    for url in parsed_query:
        uris = url['URIs']['concepts']
        for uri in uris:
            for type in core.obtain_types(uri):
                if type in dictType.keys():
                    dictType[type] += 1
                else :
                    dictType[type] = 1
        uris = url['URIs']['entitiesDisambiguated']
        for uri in uris:
            for type in core.obtain_types(uri):
                if type in dictType.keys():
                    dictType[type] += 1
                else :
                    dictType[type] = 1
