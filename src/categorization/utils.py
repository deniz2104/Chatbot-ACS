from functools import lru_cache
import torch
from src.categorization.constants import _MODEL

@lru_cache(maxsize=4096)
def _encode_single(kw: str):
    return _MODEL.encode(kw, convert_to_tensor=True)

def _encode_matrix(kws: list[str]):
    return torch.stack([_encode_single(kw) for kw in kws])
