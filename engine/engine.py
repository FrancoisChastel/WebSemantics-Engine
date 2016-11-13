#!/usr/bin/python

import sys
import json
import requests
import grequests
import time

##################
## Class Engine ##
##################

class Engine:

	# Alchemy Response Callback
	def alchemyResponseCallback(self, r, *args, **kwargs):
		try :
			url = r.url
			resultatAlchemy = r.json		
			
			# extracting Concepts
			print resultatAlchemy['concepts']
			# formatting JSON
			self.jsonOutput["Websites"].append({"URL":url,"URI":{"concepts":"test","entitiesDisambiguated":"test"}})	
		except Exception as e:
			print "Exception raised : Incorrect JSON responses. Content:"+r.text

		
	# Constructor : just initialize the empty json Output
	def __init__(self):
		self.jsonOutput = json.loads('{"Websites":[]}')
		    
		    
	# Core of the class
	def run(self, request, numberOfRequests=10):
		# Defining variables
		with open('keys.json') as data_file :  
			data = json.load(data_file)
			customSearchApiKey = data['customSearch']['apiKey']
			customSearchCx = data['customSearch']['cx']
			AlchemyApiKey = data['alchemy']['apiKey']

		# STEP 1: Send Google Request
		print "-- Getting list of URL (CustomSearch) --"
		r = requests.get( "https://www.googleapis.com/customsearch/v1?q="+request+"&key="+customSearchApiKey+"&cx="+customSearchCx)
		resultat = r.json()

		# -- extracting list of urls from JSON
		urls = []
		for element in resultat['items']:
			urls.append(element['link'])

		# STEP 2: Send to AlchimyAPI, To extract things (Formated JSON) Every lines marked with "format line" comment, do JSON formating.
		print "-- Getting informations from URLS (Alchemy) --"
		
		urlToRequest = []
		for url in urls:
		# Constructing the requets array
			urlToRequest.append("https://gateway-a.watsonplatform.net/calls/url/URLGetCombinedData?apikey="+AlchemyApiKey+"&url="+url+"&outputMode=json")
			
		rs = (grequests.get(u, hooks=dict(response=self.alchemyResponseCallback)) for u in urlToRequest)
		
		print "requests sent"
		grequests.map(rs)
		print "all responses received"
		print self.jsonOutput
	
##############
##   MAIN		##
##############

def main():
	engine = Engine()
	engine.run('paris')
	
if __name__ == "__main__":
	main()
