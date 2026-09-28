import numpy as np

from .metric import TARGET_RECALL, precision_at_recall


class PrecisionAtRecallMetric(object):
    """Метрика P@R>=0.7 из metric.py в виде eval_metric для CatBoost.
    """

    def __init__(self, recall=TARGET_RECALL):
        self.recall = recall

    def is_max_optimal(self):
        return True

    def evaluate(self, approxes, target, weight):
        score = np.array(approxes[0], dtype=float)
        y = np.array(target, dtype=int)
        return precision_at_recall(y, score, self.recall), 1.0

    def get_final_error(self, error, weight):
        return error
