#!/bin/bash

# Parsing parameters
InputRequest=$1
ApiKey=AIzaSyB55Q4tpXmOmXrRaYU2MC7IvfGRn-VQa6c 
cx=008214837905171502064:yuy4kpi9ui0


echo Request : $InputRequest

# STEP 1: Send Google Request

curl "https://www.googleapis.com/customsearch/v1?q=$InputRequest&key=$ApiKey&cx=$cx"
