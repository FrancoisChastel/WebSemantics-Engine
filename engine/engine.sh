#!/bin/bash


###############
## FUNCTIONs ##
###############

# This function checkecho "Conf file seems to be OK" if the last execution succeded and display a message.
function checkResult
{
	if [ $? -eq 0 ]; then
    echo -e "\e[32mdone\e[0m"
	else
		echo -e "\e[31mfail\e[0m"
		exit 1
	fi
}


##############
##   MAIN		##
##############


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
echo "-- Getting list of URL (CustomSearch) --"
curl -s  "https://www.googleapis.com/customsearch/v1?q=$InputRequest&key=$ApiKeyCustomSearch&cx=$cx" > Responses/customSearchResponse 
checkResult
cat Responses/customSearchResponse | jq -r .items[].link > Responses/URLs
checkResult

# STEP 2: Send to AlchimyAPI, To extract things
echo "-- Getting informations from URLS (Alchemy) --"
for line in $(cat Responses/URLs);
do 
	echo "$line..."
	curl -s -X POST -d "outputMode=json" -d "extract=entities, keywords, concepts" -d "sentiment=1" -d "maxRetreve=1" -d "url=$line" "https://gateway-a.watsonplatform.net/calls/url/URLGetCombinedData?apikey=$ApiKeyAlchemy">>Responses/AlchemyResponse; 
	checkResult
	echo "," >>Responses/AlchemyResponse; 
done  

