#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement, print_function, division
from SPARQLWrapper import SPARQLWrapper, JSON
import json


def generate_matrix(parsed_query):
    #parsed_query = json.loads(query)

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


def obtain_types(URI):
    query = '''
    SELECT * WHERE {
    <'''+URI+'''> rdf:type ?type.
    }'''

    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)
    converted_query = sparql.query().convert()

    for element in converted_query["results"]["bindings"]:
        yield element["type"]["value"]

    