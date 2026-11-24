# System design and agent review

## Roles (logical review agents, not autonomous deployed services)

1. **Extraction reviewer:** check OCR/layout completeness, section boundaries, tables, image captions and source coordinates.
2. **Graph reviewer:** verify stable IDs, provenance, citation DOI/arXiv matching, relation normalization and traversal depth.
3. **Retrieval reviewer:** evaluate graph + vector candidate recall, fusion, MaxSim reranking and answer evidence.
4. **Operations reviewer:** verify image reproducibility, secrets, volume durability, rollback, and load testing.

## Production target

PDF -> queue -> MinerU adapter -> structured blocks -> GROBID refs -> Gemini/Pydantic entities -> provenance graph Neo4j + text Chroma + ColQwen2 multivectors Qdrant + object storage. Offline citation Leiden communities and summary embeddings. Query -> router -> parallel graph/text/visual/community candidates -> RRF + learned reranker -> multimodal Gemini -> citations with paper/page/bounding-box verification -> authenticated LTI 1.3 frontend.

## Acceptance gates

- Parse gold set of 100 diverse PDFs; measure section F1, table extraction exactness, figure-caption linkage.
- Evaluate 200 manually labeled questions across shallow/deep and figure/table categories; report Recall@10, nDCG@10, citation support and hallucination rate.
- Validate idempotent ingestion, restart/retry, concurrency and corpus-scale latency.
- Test secret rotation, SSO permission boundaries, PDF abuse protection, backups and restore.

## ASU placeholder deployment

`rag.example.asu.edu` and `registry.example.asu.edu` are deliberately fictitious examples. Obtain actual registry, namespace, ingress class, storage class, LTI configuration and networking approval from your university infrastructure administrators. No deployment or institutional access is implied.
