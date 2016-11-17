#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement, print_function, division
from SPARQLWrapper import SPARQLWrapper, JSON
import json



def generate_matrix(parsed_query):
    return compute_similarities(parsed_query['Websites'])


def compute_similarities(parsed_query):
    similarities_matrix = [[0 for i in range(len(parsed_query))] for j in range(len(parsed_query))]

    for index, element in enumerate(parsed_query):
        for p_index, compare_to in enumerate(parsed_query):
            if index == p_index:
                similarities_matrix[index][p_index] = 1
            else:
                similarities_matrix[index][p_index] = compute_similarity(element, compare_to)
    return similarities_matrix


def compute_similarity(element,
                       compare_to,
                       weight_concepts=1,
                       weight_disambiguated=1):
    element = element["URI"]
    compare_to = compare_to["URI"]

    return (((weight_concepts) * (len(set(element["concepts"]).intersection(set(compare_to["concepts"])))
                                  / max(len(element["concepts"]), len(compare_to["concepts"]))))
            + ((weight_disambiguated) * (
        len(set(element["entitiesDisambiguated"]).intersection(set(compare_to["entitiesDisambiguated"])))
        / max(len(element["entitiesDisambiguated"]), len(
            compare_to["entitiesDisambiguated"]))))) / (weight_disambiguated + weight_concepts)


#def obtain_bests_predicates(URI,
#                            URIs):
#    for element in obtain_same_type(URI):
#        for attributes in obtain_attributes(element):


#################
#   SPARQL API  #
#################
def obtain_attributes(URI):
    query = "SELECT ?data WHERE { <"+URI+"> ?data ?o. FILTER(lang(?o) = '' || lang(?o) = 'en'). }"

    response = query_sparql(query)

    for element in response["results"]["bindings"]:
        yield element["data"]["value"]


def obtain_same_type(URI):
    query = "SELECT * WHERE {{ ?same_type rdf:type {}. }}".format(" ; ".join(obtain_types(URI)))

    response = query_sparql(query)

    for element in response["results"]["bindings"]:
        yield element["same_type"]["value"]


def obtain_types(URI):
    query = '''
    SELECT * WHERE {
    <'''+URI+'''> rdf:type ?type.
    }'''
    response = query_sparql(query)

    for element in response["results"]["bindings"]:
        yield element["type"]["value"]


def query_sparql(query):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)

   return sparql.query().convert()
