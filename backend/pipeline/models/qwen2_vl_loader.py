import torch
import gc
import json
import re
from PIL import Image
from pathlib import Path
from typing import Dict, Any
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

class Qwen2VLLoader:
    def __init__(self, model_name: str = "/home/spai0432/ADEASY_SHORTS/models/Qwen2-VL-7B"):
        self.model_name = model_name
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🎯 Qwen2-VL will use device: {self.device}")
    
    def load(self):
        if self.model is not None:
            return
        
        print(f"🔄 Loading Qwen2-VL from {self.model_name}...")
        try:
            # Min_pixels/Max_pixels 설정으로 이미지 인식률 향상
            self.processor = AutoProcessor.from_pretrained(
                self.model_name, 
                min_pixels=256*256, 
                max_pixels=1280*1280
            )
            
            # L4 GPU 최적화 (bfloat16)
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=torch.bfloat16,
                device_map="auto",
            )
            print(f"✅ Qwen2-VL loaded on {self.device}")
        except Exception as e:
            print(f"❌ Failed to load Qwen2-VL: {e}")
            raise
    
    def unload(self):
        if self.model is not None:
            del self.model
            del self.processor
            self.model = None
            self.processor = None
            gc.collect()
            torch.cuda.empty_cache()
            print("🗑️ Qwen2-VL unloaded")

    def analyze_product(self, image_path: str, prompt_template: str = None) -> Dict[str, Any]:
        if self.model is None:
            self.load()

        # 1. 이미지 로드 (RGB 변환)
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            print(f"❌ Image Error: {e}")
            return {"error": str(e)}

        # 2. 프롬프트 (예시 제거 -> 베끼기 방지)
        if prompt_template is None:
            prompt_template = """Analyze this product image accurately.
            
            Return ONLY a JSON object with these keys:
            - category: (e.g., hoodie, shirt, jacket)
            - colors: (list of visible colors)
            - style: (e.g., casual, formal, sporty)
            - keywords: (list of 5 visual traits)
            - description: (short description of the item)
            
            Do not include any other text. Just the JSON."""

        # 3. 메시지 구성
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt_template},
                ],
            }
        ]

        # 4. vision info 처리 (핵심!)
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)
        
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        ).to(self.device)

        # 5. 추론
        print(f"🤔 Analyzing: {Path(image_path).name}")
        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs, 
                max_new_tokens=512,
                do_sample=False  # Deterministic (더 정확하게)
            )
        
        # 6. 결과 디코딩
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]

        return self._parse_response(output_text)

    def _parse_response(self, text: str) -> Dict[str, Any]:
        # JSON 파싱 시도
        try:
            # 마크다운 코드블록 제거
            clean_text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except:
            # 실패 시 원본 텍스트 반환 (디버깅용)
            print(f"⚠️ JSON Parse Failed. Raw text: {text}")
            return {
                "description": text,
                "category": "unknown",
                "colors": [],
                "style": "unknown",
                "keywords": []
            }

# 싱글톤 인스턴스
_qwen2vl_loader = None
def get_qwen2vl_loader():
    global _qwen2vl_loader
    if _qwen2vl_loader is None:
        _qwen2vl_loader = Qwen2VLLoader()
    return _qwen2vl_loader
