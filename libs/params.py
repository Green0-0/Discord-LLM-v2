# Contains all the sampling parameters: temperature, min-p, top-p, top-k, repetition-penalty, max-new-tokens
class Params:
    name : str
    temperature : float
    min_p : float
    top_p : float
    top_k : int
    repetition_penalty : float
    max_new_tokens : int

    def __init__(self, name : str, temperature : float = 1, min_p : float = 0.15, top_p : float = 1, top_k : int = 0, repetition_penalty : float = 0, max_new_tokens : int = 500):
        self.name = name
        self.temperature = temperature
        self.min_p = min_p
        self.top_p = top_p
        self.top_k = top_k
        self.repetition_penalty = repetition_penalty
        self.max_new_tokens = max_new_tokens