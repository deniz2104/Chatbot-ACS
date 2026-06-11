from collections.abc import Callable
from pathlib import Path
from typing import Optional, Union

def download(model_name: str, model_path: Union[str, Path], token: Optional[str] = None):
    from huggingface_hub import snapshot_download
    snapshot_download(repo_id=model_name, local_dir=str(model_path), token=token)

def load(library: Callable, model_path: Union[str, Path], max_length: Optional[int] = None):
    kwargs = {"max_length": max_length} if max_length is not None else {}
    return library(str(model_path), **kwargs)
