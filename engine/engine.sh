#!/bin/bash

# Parsing parameters
if [ -z ${1+x} ]; 
	then 
		echo "Please specify à query. Example : ./engine.sh \"Kurt Cobain\""; 
		exit 1;
fi

InputRequest=$1


# Defining variables
ApiKeyCustomSearch=`cat keys | jq -r .customSearch.apiKey`
cx=`cat keys | jq -r .customSearch.cx`
ApiKeyAlchemy=`cat keys | jq -r .alchemy.apiKey`


# STEP 1: Send Google Request
curl "https://www.googleapis.com/customsearch/v1?q=$InputRequest&key=$ApiKeyCustomSearch&cx=$cx" > Responses/customSearchResponse 
cat Responses/customSearchResponse | jq -r .items[].link > Responses/URLs


# STEP 2: Send to AlchimyAPI. To extract things
for line in $(cat Responses/URLs);
do 
	curl -X POST -d "outputMode=json" -d "extract=entities,keywords" -d "sentiment=1" -d "maxRetreve=1" -d "$line" "https://gateway-a.watsonplatform.net/calls/url/URLGetCombinedData?apikey=$ApiKeyAlchemy">>Responses/AlchemyResponse; 
done  

