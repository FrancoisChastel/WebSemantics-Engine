from flask import Flask
from flask import request
import urifactory.URIFactory as URIFactory
import sel.core as core
import pertinenceengine.pertinenceEngine as PertinenceEngine
import similariteengine.similariteEngine as SimilariteEngine
from SPARQLWrapper import SPARQLWrapper, JSON
import json
import logging

app = Flask(__name__)


@app.route('/getResults')
def findResults():
    return 'H'


@app.route('/infoURI', methods=['GET', 'POST'])
def findInfoUri():
    uri = request.form['uri']
    response = list()

    for value in core.obtain_revelant_attributes(uri):
        miniDict = dict()
        miniDict['attribut'] = value[0]
        miniDict['valeur'] = value[1]
        response.append(miniDict)
    return json.dumps(response)


def generate_json(query):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    engined = engine.Engine()
    parsed_query = engined.run(query)
    parsed_query = parsed_query['Websites']
    alimentByType(parsed_query)
    dictType = dict()
    evaluateType(dictType, parsed_query)

    to_return = json.dumps(data_json)
    return to_return


@app.route('/search/<query>')
def search(query):
    # -- Pipeline --
    # URIFactory
    urifactory = URIFactory.URIFactory()
    outputJson = urifactory.run(query)
    parsed_query = outputJson['Websites']
    logging.info('Step 1 : Done')

    # TypeFactory
    alimentByType(parsed_query)
    logging.info('Step 2 : Done')

    # TypeRanker
    evaluated_types = dict()
    evaluateType(evaluated_types, parsed_query)
    outputJson['typeRank'] = evaluated_types
    logging.info('Step 3 : Done')

    # Pertinence
    pertinenceEngine = PertinenceEngine.PertinenceEngine(outputJson)
    outputJson = pertinenceEngine.run()
    logging.info('Step 4 : Done')

    # Similarity
    similariteEngine = SimilariteEngine.SimilariteEngine(outputJson)
    result = similariteEngine.run()
    outputJson["similarities"] = result
    # print json.dumps(outputJson)
    return outputJson


def alimentByType(parsed_query):
    for url in parsed_query:
        uris = url["URIs"]
        for i, uri in enumerate(uris):
            name = uri
            uri = dict()
            uri['name'] = name
            uri['types'] = list()
            for typed in core.obtain_types(name):
                uri['types'].append(typed)
            uris[i] = uri
    return parsed_query


def evaluateType(dictType, parsed_query):
    for url in parsed_query:
        uris = url['URIs']
        for uri in uris:
            for typed in uri['types']:
                if typed in dictType.keys():
                    dictType[typed] += 1
                else:
                    dictType[typed] = 1
