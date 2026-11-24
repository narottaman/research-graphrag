from pathlib import Path
from functools import lru_cache
from app.config import settings
# ColQwen2 optional, GPU intensive. Patch-vector dimension is model-dependent.
@lru_cache(maxsize=1)
def model_and_processor():
    import torch
    from transformers import ColQwen2ForRetrieval, ColQwen2Processor
    model=ColQwen2ForRetrieval.from_pretrained(settings.visual_model,torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,device_map="auto").eval()
    processor=ColQwen2Processor.from_pretrained(settings.visual_model)
    return model,processor

def encode_image(path: str):
    import torch
    from PIL import Image
    model,proc=model_and_processor()
    batch=proc.process_images([Image.open(path).convert("RGB")]).to(model.device)
    with torch.no_grad():vectors=model(**batch).embeddings[0].float().cpu().tolist()
    return vectors

def encode_query(text: str):
    import torch
    model,proc=model_and_processor()
    batch=proc.process_queries([text]).to(model.device)
    with torch.no_grad():vectors=model(**batch).embeddings[0].float().cpu().tolist()
    return vectors
