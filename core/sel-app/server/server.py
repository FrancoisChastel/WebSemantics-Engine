from flask import Flask
import engine.engine as engine
import sel.core as core
import json

app = Flask(__name__)

@app.route('/getResults')
def findResults():

    return 'H'


def generate_json(query):
    engined = engine.Engine()
    dictUrlUri = engined.run(query)
    #matrix = generate_matrix(query)
    #matrix = [[[1],[0.4],[0.3],[0.6]],[[0.3],[1],[0.1],[0.5]],[[0.2],[0.4],[1],[0.6]],[[0.7],[0.3],[0.1],[1]]]
    matrix = core.generate_matrix(dictUrlUri)
    #parse query
    #parsed_query = json.loads(query)
    parsed_query = query['Websites']
    data_json = dict()
    listOfURL = list()
    for i, val in enumerate(matrix):
        print(val) 
    for j, target in enumerate(val):
            link = dict()
            print(j , target)
            link['weight'] = target 
            link['urls'] = [parsed_query[i]['URL'], parsed_query[j]['URL']]
            listOfURL.append(link)
#            print(listOfURL)

    data_json['link_url'] = listOfURL
            
    to_return =  json.dumps(data_json)
    return to_return

def associate(cle, value):
    return {cle : value}

def append(cle, value):
    return cle.append(value)
