#!/bin/sh
set -eu
REGISTRY="${REGISTRY:-registry.example.asu.edu/research}"
TAG="${TAG:-0.1.0}"
docker build -f Dockerfile -t "$REGISTRY/rag-api:$TAG" .
docker build -f Dockerfile.worker -t "$REGISTRY/rag-worker:$TAG" .
docker push "$REGISTRY/rag-api:$TAG"
docker push "$REGISTRY/rag-worker:$TAG"
