#!/usr/bin/python

import json
import sys


class URLLink:
    def __init__(self, URLFrom, URLto):
        self.URLFrom = URLFrom
        self.URLto = URLto
        self.uris = {}

    def setBest(self, uri, score):
        if uri not in self.uris.keys():
            self.uris[uri] = score
        else:
            if score > self.uris[uri]:
                self.uris[uri] = score

    def calculerAVG(self):
        count = 0.0
        sommedecalcule = 0.0
        for key, value in self.uris.items():
            count += 1
            sommedecalcule += float(value)
        return float(sommedecalcule / count)


############################
## Class PertinenceEngine ##
############################

class SimilariteEngine:
    # Constructor : just initialize the empty json Output
    def __init__(self, inputMap):
        self.outputMap = inputMap

    # buildMatrix of URIs Mapping
    def buildingMatrix(self):

        # DefiningMatrix
        Matrix = {}

        # Core
        for websiteX in self.outputMap["Websites"]:  # Boucle de parcours des URL X
            urlX = websiteX["URL"]
            for uriX in websiteX["URIs"]:  # boucle de parcours de URI X
                for websiteY in self.outputMap["Websites"]:  # Boucle de parcours des URL Y
                    urlY = websiteY["URL"]
                    for uriY in websiteY["URIs"]:

                        if urlX not in Matrix:
                            Matrix[urlX] = dict()

                        if urlY not in Matrix[urlX]:
                            Matrix[urlX][urlY] = URLLink(urlX, urlY)

                        Matrix[urlX][urlY].setBest(uriX["name"], self.CompareUris(uriX, uriY))
        return Matrix

    # Compare 2 Uris
    def CompareUris(self, URI1, URI2):
        tabType1 = URI1["types"]
        tabType2 = URI2["types"]

        intersection = float(len(set(tabType1).intersection(set(tabType2))))
        allSize = float((len(tabType1) + len(tabType2)) - intersection)

        if allSize == 0:
            return 0
        return float(intersection / allSize)

    def run(self):
        URIMatrix = self.buildingMatrix()
        liste = []
        for urlX, Dict in URIMatrix.items():
            for urlY, Obj in Dict.items():
                liste.append({"from": urlX, "to": urlY, "weight": Obj.calculerAVG()})
        return liste
