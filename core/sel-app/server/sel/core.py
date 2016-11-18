#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement, print_function, division

from collections import Counter

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


def obtain_revelant_attributes(URI):
    def transform_obtain_bests_predicates(URI):
        for element in obtain_bests_predicates(URI):
            yield " OPTIONAL{ <"+URI+"> <"+element+"> ?"+str(element).split("/")[-1].replace("#", "")+" }"

    query = "SELECT * WHERE {{ {} }}".format(" ".join(transform_obtain_bests_predicates(URI)))

    response = query_sparql(query)

    for var in response["head"]["vars"]:
        if var in response["results"]["bindings"][0]:
            yield (var,response["results"]["bindings"][0][var]["value"])

def obtain_bests_predicates(URI,
                            top=20):
    redundancy = Counter()

    for element in obtain_same_type(URI):
        for attributes in obtain_attributes(element):
            redundancy[attributes] += 1

    current_top = 0
    for element in redundancy.most_common():
        if element[1] < 1000:
            current_top+=1
            yield element[0]
        if current_top >= top:
            break

#################
#   SPARQL API  #
#################
def obtain_attributes(URI):
    query = "SELECT ?data WHERE { <"+URI+"> ?data ?o. }"

    response = query_sparql(query)

    for element in response["results"]["bindings"]:
        yield element["data"]["value"]


def obtain_same_type(URI):
    query = "SELECT * WHERE {{ ?same_type rdf:type <{}>. }} LIMIT 1000".format("> , <".join(obtain_best_types(URI)))

    response = query_sparql(query)

    for element in response["results"]["bindings"]:
        yield element["same_type"]["value"]


def obtain_best_types(URI,
                      top=10):
    current_top = 0
    for element in obtain_types(URI):
        current_top+=1
        if top <= current_top :
            break
        yield element


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
