"""
Embedding Utilities - TF-IDF based text similarity for query ranking
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_vectorizer = None


def get_vectorizer():
    """Get or create TF-IDF vectorizer."""
    global _vectorizer
    if _vectorizer is None:
        _vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2),
            max_features=5000,
        )
    return _vectorizer


def calculate_query_similarities(queries: list[str], cv_text: str) -> np.ndarray:
    """Calculate TF-IDF cosine similarities between queries and CV text."""
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words='english',
        ngram_range=(1, 2),
        max_features=5000,
    )

    all_texts = [cv_text] + queries
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    cv_vector = tfidf_matrix[0:1]
    query_vectors = tfidf_matrix[1:]

    similarities = cosine_similarity(query_vectors, cv_vector).flatten()
    return similarities


def embed_text(text: str) -> np.ndarray:
    """Generate TF-IDF vector for text (for backwards compatibility)."""
    vectorizer = get_vectorizer()
    return vectorizer.fit_transform([text]).toarray()[0]


def embed_texts(texts: list[str]) -> np.ndarray:
    """Generate TF-IDF vectors for multiple texts."""
    vectorizer = get_vectorizer()
    return vectorizer.fit_transform(texts).toarray()


def calculate_similarities(query_embeddings: np.ndarray, cv_embedding: np.ndarray) -> np.ndarray:
    """Calculate cosine similarities (for backwards compatibility)."""
    dot_products = np.dot(query_embeddings, cv_embedding)
    query_norms = np.linalg.norm(query_embeddings, axis=1)
    cv_norm = np.linalg.norm(cv_embedding)
    if cv_norm == 0:
        return np.zeros(len(query_embeddings))
    similarities = dot_products / (query_norms * cv_norm + 1e-10)
    return similarities
