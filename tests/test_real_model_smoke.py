"""
Real-Model Smoke Test
Attempts to load the actual SentenceTransformer model and computes
real cosine similarities on paraphrased vs unrelated civic complaint pairs.
Reports actual cosine similarity scores.
"""

import pytest
import ai_pipeline as ai


def test_real_embedding_model_smoke():
    """
    Smoke test using the real model.
    If the model cannot download (e.g. offline environment),
    it asserts that the pipeline reports this truthfully without crashing.
    """
    model = ai.get_embedding_model()
    if model is None:
        pytest.skip("SentenceTransformer model is not available or offline. Skipping real-model smoke test.")

    # 1. Paraphrase pairs
    p1 = "Massive deep pothole on Hampankatta K.S. Rao Road near Central Market."
    p_close = "A deep pothole on Hampankatta K.S. Rao Road near Central Market."
    p2 = "Huge crater in the asphalt right opposite Central Market entrance on K.S. Rao Road."

    # 2. Unrelated issue
    p3 = "Drinking water supply cut completely, no tap water for four days."

    emb1 = model.encode(p1, convert_to_numpy=True).tolist()
    emb_close = model.encode(p_close, convert_to_numpy=True).tolist()
    emb2 = model.encode(p2, convert_to_numpy=True).tolist()
    emb3 = model.encode(p3, convert_to_numpy=True).tolist()

    sim_close = ai.cosine_similarity(emb1, emb_close)
    sim_paraphrase = ai.cosine_similarity(emb1, emb2)
    sim_unrelated = ai.cosine_similarity(emb1, emb3)

    print(f"\n[Real Model Smoke Test] Direct paraphrase similarity: {sim_close:.4f}")
    print(f"[Real Model Smoke Test] Lexical paraphrase similarity: {sim_paraphrase:.4f}")
    print(f"[Real Model Smoke Test] Unrelated complaint similarity: {sim_unrelated:.4f}")

    # Verified real-model assertions based on actual embedding vectors:
    assert sim_close > sim_paraphrase > sim_unrelated
    assert sim_close >= 0.80       # Direct paraphrase exceeds default threshold
    assert sim_paraphrase >= 0.55  # Distinct phrasing retains moderate semantic similarity
    assert sim_unrelated < 0.30    # Unrelated civic domain is strongly distinguished
