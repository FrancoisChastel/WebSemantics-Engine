from flask import Flask
import URIFactory.URIFactory as engine
import sel.core as core
from SPARQLWrapper import SPARQLWrapper, JSON
import json

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
    #matrix = generate_matrix(query)
    #matrix = [[[1],[0.4],[0.3],[0.6]],[[0.3],[1],[0.1],[0.5]],[[0.2],[0.4],[1],[0.6]],[[0.7],[0.3],[0.1],[1]]]
    #matrix = core.generate_matrix(dictUrlUri)
    #parse query
    #parsed_query = json.loads(query)
    parsed_query = parsed_query['Websites']
    alimentByType(parsed_query)
    dictType = dict()
    evaluateType(dictType,parsed_query)

    
    
            
    to_return =  json.dumps(data_json)
    return to_return


def test(query):
    engined = engine.Engine()
    query = engined.run(query)
    parsed_query = query['Websites']
    alimentByType(parsed_query)
    evaluated_types = dict()
    evaluateType(evaluated_types,parsed_query)
    query['typeRank'] = evaluated_types
    return query




def alimentByType(parsed_query):
    for url in parsed_query:
        uris = url["URIs"]
        for i , uri in enumerate(uris):
            name = uri
            uri = dict()
            uri['name'] = name
            uri['types'] = list()
            for typed in core.obtain_types(name):
                uri['types'].append(typed)
            uris[i] = uri
    return parsed_query



def evaluateType(dictType,parsed_query):
    for url in parsed_query:
        uris = url['URIs']
        for uri in uris:
            for typed in uri['types'] :
                if typed in dictType.keys():
                    dictType[typed] += 1
                else :
                    dictType[typed] = 1