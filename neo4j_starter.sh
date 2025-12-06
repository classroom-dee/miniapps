#!/bin/bash

set -a
source .env
set +a

name=neo4j-test

docker run -d --rm \
  --name $name \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=$NEO4J_USER/$NEO4J_PW \
  -v neo4j-test-volume:/data \
  neo4j:5.26.9-community

