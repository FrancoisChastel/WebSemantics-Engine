#!/usr/bin/python

import sys
import json
import requests
import grequests

##################
## Class Engine ##
##################

class Engine:

	def alchemyResponseCallback(response):
		print "Response"
		self.jsonOuput["Websites"].append("done")		
		
	def __init__(self):
		self.jsonOutput = json.dumps({'Websites':[]})
		    
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
	
		urls = []
		for element in resultat['items']:
			urls.append(element['link'])

		# STEP 2: Send to AlchimyAPI, To extract things (Formated JSON) Every lines marked with "format line" comment, do JSON formating.
		print "-- Getting informations from URLS (Alchemy) --"
		
		asyncRequests = []
		for url in urls:
		# Constructing the requets array
			urlToRequest = "https://gateway-a.watsonplatform.net/calls/url/URLGetCombinedData?apikey="+AlchemyApiKey+"&url="+url
			asyncRequests.append(grequests.get(urlToRequest,hooks=dict(response=alchemyResponseCallback))
		
		grequests.send(asyncRequests)
		print 'Requests sent'
	
##############
##   MAIN		##
##############

def main():
	engine = Engine()
	engine.run('paris')
	
if __name__ == "__main__":
	main()
