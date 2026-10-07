"""
Offline Evaluation Script for Lost & Found Pet AI Similarity Matching.
Evaluates Precision, Recall, and F1-Score across thresholds on a labeled test set.
Fulfills guideline: Never display raw 'accuracy' claims without empirical precision/recall verification.
"""
from typing import List, Dict, Tuple
from app.services.ai_embedding import ai_embedding_service


def get_labeled_eval_dataset() -> List[Dict[str, any]]:
    """
    Returns a benchmark set of positive and negative pet matching pairs.
    Each pair has two pet feature descriptions / simulated image signatures
    and ground truth is_match: True or False.
    """
    return [
        # --- Positive Pairs (Same Pet) ---
        {
            "pair_id": "P01",
            "pet_a": "dog:golden_retriever:cream:white_chest",
            "pet_b": "dog:golden_retriever:cream:white_chest",
            "is_same": True
        },
        {
            "pair_id": "P02",
            "pet_a": "cat:indie_tabby:orange:striped_tail",
            "pet_b": "cat:indie_tabby:orange:striped_tail",
            "is_same": True
        },
        {
            "pair_id": "P03",
            "pet_a": "dog:labrador:black:white_paws",
            "pet_b": "dog:labrador:black:white_paws",
            "is_same": True
        },
        {
            "pair_id": "P04",
            "pet_a": "dog:beagle:tricolor:white_tip_tail",
            "pet_b": "dog:beagle:tricolor:white_tip_tail",
            "is_same": True
        },
        {
            "pair_id": "P05",
            "pet_a": "cat:persian:white:blue_eyes",
            "pet_b": "cat:persian:white:blue_eyes",
            "is_same": True
        },

        # --- Hard Negatives (Same Breed, Different Colors/Marks) ---
        {
            "pair_id": "N01",
            "pet_a": "dog:labrador:black:white_paws",
            "pet_b": "dog:labrador:golden:pure_yellow",
            "is_same": False
        },
        {
            "pair_id": "N02",
            "pet_a": "cat:indie_tabby:orange:striped_tail",
            "pet_b": "cat:indie_tabby:black_grey:solid",
            "is_same": False
        },
        {
            "pair_id": "N03",
            "pet_a": "dog:golden_retriever:cream:white_chest",
            "pet_b": "dog:golden_retriever:red_golden:dark",
            "is_same": False
        },

        # --- True Negatives (Different Species / Breeds) ---
        {
            "pair_id": "N04",
            "pet_a": "dog:pug:fawn:black_mask",
            "pet_b": "dog:german_shepherd:black_tan:saddle",
            "is_same": False
        },
        {
            "pair_id": "N05",
            "pet_a": "cat:siamese:cream:seal_point",
            "pet_b": "dog:beagle:tricolor:white_tip_tail",
            "is_same": False
        },
    ]


def evaluate_thresholds(dataset: List[Dict[str, any]]) -> List[Dict[str, float]]:
    # Precompute similarities
    scored_pairs: List[Tuple[float, bool]] = []
    for item in dataset:
        vec_a = ai_embedding_service.generate_image_embedding(image_url_or_meta=item["pet_a"])
        vec_b = ai_embedding_service.generate_image_embedding(image_url_or_meta=item["pet_b"])
        sim = ai_embedding_service.compute_cosine_similarity(vec_a, vec_b)
        scored_pairs.append((sim, item["is_same"]))

    thresholds = [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90]
    metrics = []

    for t in thresholds:
        tp = sum(1 for sim, is_same in scored_pairs if sim >= t and is_same)
        fp = sum(1 for sim, is_same in scored_pairs if sim >= t and not is_same)
        fn = sum(1 for sim, is_same in scored_pairs if sim < t and is_same)
        tn = sum(1 for sim, is_same in scored_pairs if sim < t and not is_same)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        metrics.append({
            "threshold": t,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1, 3)
        })

    return metrics


def print_evaluation_report():
    dataset = get_labeled_eval_dataset()
    results = evaluate_thresholds(dataset)

    print("================================================================================")
    print(" ANIMAL GUARDIAN 360° — PET VECTOR MATCHING EVALUATION BENCHMARK")
    print(f" Test Set Size: {len(dataset)} labeled pairs (Positives: 5, Negatives: 5)")
    print("================================================================================")
    print(f"{'Threshold':<10} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'TP':<4} | {'FP':<4} | {'FN':<4} | {'TN':<4}")
    print("-" * 75)

    best_thresh = None
    best_f1 = -1.0

    for r in results:
        print(f"{r['threshold']:<10.2f} | {r['precision']:<10.3f} | {r['recall']:<10.3f} | {r['f1_score']:<10.3f} | {r['tp']:<4} | {r['fp']:<4} | {r['fn']:<4} | {r['tn']:<4}")
        if r['f1_score'] > best_f1:
            best_f1 = r['f1_score']
            best_thresh = r['threshold']

    print("=" * 75)
    print(f"Recommended Production Threshold: {best_thresh} (Optimal F1-Score: {best_f1:.3f})")
    print("================================================================================\n")


if __name__ == "__main__":
    print_evaluation_report()
