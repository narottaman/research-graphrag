# Kubernetes deployment (illustrative only)

The manifests deploy only the API, worker, and shared PVC. Provision Neo4j, Chroma, Qdrant, Redis and GROBID separately as managed services or stateful workloads with durable storage and backups. Replace all `example.asu.edu` hosts and registry paths; no ASU infrastructure is verified. Cluster must provide an RWX storage class and ingress controller. A production deployment must add authentication, rate limits, NetworkPolicies, secrets management, TLS, backup/restore and monitoring.

```sh
kubectl apply -f k8s/namespace.yaml
kubectl -n research-rag create secret generic rag-secrets --from-literal=NEO4J_PASSWORD='REPLACE' --from-literal=GEMINI_API_KEY='REPLACE'
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/app.yaml
kubectl apply -f k8s/ingress.yaml
kubectl -n research-rag rollout status deployment/rag-api
```
