# RAG evaluation

| Metric | Value |
|---|---|
| Retrieval Recall@3 (12 hand-written queries) | 1.0 |
| Faithfulness: explanations whose numbers all appear in the context | 1.0 (18/20 requests answered by the LLM) |
| Explanations that name the rank-1 vendor | 1.0 |

Faithfulness is checked automatically: every number in the generated text must appear in the context given to the model (small list markers excepted). Failing texts are replaced by the template explanation in the app, so users never see an unverified number.

Vector store used for this run: `numpy-fallback`.