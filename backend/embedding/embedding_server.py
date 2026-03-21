import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import torch
import torch.nn.functional as F
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Union, List
from transformers import AutoModel, AutoTokenizer
import uvicorn

# 1. 配置你的本地模型路径
MODEL_PATH = "D:\\workspace\\Qwen3-Embedding-0.6B"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"正在加载模型到 {DEVICE}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModel.from_pretrained(
    MODEL_PATH,
    dtype=torch.float16,
    device_map=DEVICE,
)
model.eval()
print("模型加载完成！")

# 2. 初始化 FastAPI
app = FastAPI(title="Qwen3 Embedding API (OpenAI Compatible)")

# 定义 OpenAI 请求体的数据模型
class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: str = "qwen3-embedding"

@app.post("/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    # 处理单个文本或文本列表
    texts = request.input if isinstance(request.input, list) else [request.input]
    
    # 3. 使用 transformers 进行分词和推理
    inputs = tokenizer(texts, padding=True, truncation=True, max_length=8192, return_tensors="pt")
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model(**inputs)
        # 获取最后一层隐状态
        last_hidden_state = outputs.last_hidden_state
        # 使用 mean pooling (Qwen embedding 通常使用均值池化或 CLS token)
        attention_mask = inputs['attention_mask']
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
        sum_embeddings = torch.sum(last_hidden_state * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        embeddings = sum_embeddings / sum_mask
        
        # 归一化 (L2 Normalize)，对余弦相似度计算很重要
        embeddings = F.normalize(embeddings, p=2, dim=1)
        
    embeddings_list = embeddings.cpu().tolist()

    # 4. 组装成严格兼容 OpenAI 格式的 JSON 返回
    response_data = []
    for i, emb in enumerate(embeddings_list):
        response_data.append({
            "object": "embedding",
            "embedding": emb,
            "index": i
        })

    return {
        "object": "list",
        "data": response_data,
        "model": request.model,
        "usage": {
            "prompt_tokens": inputs['input_ids'].numel(),
            "total_tokens": inputs['input_ids'].numel()
        }
    }

if __name__ == "__main__":
    # 启动服务器，端口设为 8830
    uvicorn.run(app, host="0.0.0.0", port=8830)