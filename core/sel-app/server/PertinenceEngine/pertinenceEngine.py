#!/usr/bin/python

import json
import sys

############################
## Class PertinenceEngine ##
############################

class PertinenceEngine:
# Constructor : just initialize the empty json Output
	def __init__(self, inputMap):
		self.outputMap = inputMap

	def run(self) :
		# Sum of Type of each URI
		for websites in self.outputMap["websites"] :
			for uri in websites["URIs"]["concepts"] :
				sum = 0;
				for typeCur in uri["types"] :
					sum = sum + self.outputMap["typeRank"].get(typeCur, 0); # summing all type
				uri["sum"] = sum
		
		print json.dumps(self.outputMap)

def main():
	# Buidling the demo Map
	map	={"websites": [{"URL": "https://en.wikipedia.org/wiki/Paris","URIs": {"concepts": [{"name": "http://dbpedia.org/resource/5th_arrondissement_of_Paris","types":["type1", "type2", "type3", "Type3", "Type4"]}, {"name": "http://dbpedia.org/resource/5th_arrondissement_of_Paris","types": ["Ville", "Type1", "Type2", "Type3", "Type4"]},{"name": "http://dbpedia.org/resource/5th_arrondissement_of_Paris","types":  ["Ville", "Type1", "Type2", "Type3", "Type4"]}],"entitiesDisambiguated": [{"name":"http://dbpedia.org/resource/5th_arrondissement_of_Paris","types":  ["Ville", "Type1", "Type2", "Type3", "Type4"]},{"name": "http://dbpedia.org/resource/5th_arrondissement_of_Paris","types":  ["type1", "type2", "type3", "Type3", "Type4"]}]}},{"URL": "https://en.wikipedia.org/wiki/Paris","URIs": {"concepts": [{"name": "http://dbpedia.org/resource/5th_arrondissement_of_Paris","types":  ["Ville", "Type1","Type2", "Type3", "Type4"]}, {"name": "http://dbpedia.org/resource/5th_arrondissement_of_Paris","types":  ["Ville", "Type1", "Type2", "Type3", "Type4"]},{"name": "http://dbpedia.org/resource/5th_arrondissement_of_Paris","types":["Ville", "Type1", "Type2", "Type3", "Type4"]}],"entitiesDisambiguated": [{	"name": "http://dbpedia.org/resource/5th_arrondissement_of_Paris","types":["Ville", "Type1", "Type2", "Type3", "Type4"]	},{"name": "http://dbpedia.org/resource/5th_arrondissement_of_Paris","types":["type1", "type2", "type3", "Type3", "Type4"]}]}}],	"typeRank": {"type1":3,"type2":1,"type3":2,"type4":4}}
	pertinenceEngine = PertinenceEngine(map)
	pertinenceEngine.run()

if __name__ == "__main__":
    main()
