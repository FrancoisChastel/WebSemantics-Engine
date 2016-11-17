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

# Variables
isDebug=false
nbResponses=10

# Parsing parameters
#--------------------- Boucle de traitement des paramètres-----------------------

for ((o=1; $#; o++))
	do
		case $1 in
        -d)
           isDebug=true           
           ;;
			  -n)
			   	nbResponses=$2;
			     ;;
				-h)
					echo -e "SYNTAXE: ./engine.sh [OPTIONS] request \nOPTIONS: \n\t-d unable debug (print verbose on stdout) \n \t-n [number of responses] \n" 
					exit 0
					;;
				*)
					InputRequest=$1
					;;
			esac
		shift;
	done



if [ -z ${InputRequest+x} ]; 
	then 
		echo "Please specify à query. Example : ./engine.sh \"Kurt Cobain\""; 
		exit 1;
fi



# -------------------- Script Begin --------------------------------------

# Defining variables
ApiKeyCustomSearch=`cat keys.json | jq -r .customSearch.apiKey`
cx=`cat keys.json | jq -r .customSearch.cx`
ApiKeyAlchemy=`cat keys.json | jq -r .alchemy.apiKey`

# STEP 1: Send Google Request
echo "-- Getting list of URL (CustomSearch) --"
curl -s  "https://www.googleapis.com/customsearch/v1?q=$InputRequest&key=$ApiKeyCustomSearch&cx=$cx" > Responses/customSearchResponse 
checkResult
cat Responses/customSearchResponse | jq -r .items[].link > Responses/URLs
checkResult

# STEP 2: Send to AlchimyAPI, To extract dbPedia URIs
echo "-- Getting informations from URLS (Alchemy) --"
echo "{\"websites\":[" > Responses/tmpUrlUri # format line

for line in $(cat Responses/URLs);
do 
	echo "{\"URL\":\"$line\"," >> Responses/tmpUrlUri # format line
	echo "$line..."

	JsonResult=$(curl -s -X POST -d "outputMode=json" -d "url=$line" "https://gateway-a.watsonplatform.net/calls/url/URLGetCombinedData?apikey=$ApiKeyAlchemy")
	checkResult
	echo $JsonResult > Responses/Alchemy

	echo "\"URIs\":{ \"concepts\":"			 >> Responses/tmpUrlUri	 # format line
	echo $JsonResult | jq -r '[.concepts[].dbpedia]' >> Responses/tmpUrlUri # format line
	echo ", \"entitiesDisambiguated\":" 		 >> Responses/tmpUrlUri # format line
	echo $JsonResult | jq -r '[.entities[].disambiguated | select(.dbpedia!=null) | .dbpedia]' >> Responses/tmpUrlUri # format line
	echo "}}" >> Responses/tmpUrlUri # format line
	echo ","  >> Responses/tmpUrlUri # format line
done  

# Delete the last Line which contains a , (because of last loop)
head -n -1 Responses/tmpUrlUri > tmp.txt ; mv tmp.txt Responses/tmpUrlUri # format line
echo "]}"  >> Responses/tmpUrlUri # format line

cat Responses/tmpUrlUri | jq . > Responses/FormatedUrlUri # format line

rm Responses/tmpUrlUri


