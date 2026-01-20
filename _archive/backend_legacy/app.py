# backend/app.py
"""
Flask REST API for ADEASY_SHORTS
[UPDATED] UI 테스트용 백엔드
- Step 0: Agentic 배경 제거 (다중 이미지)
- Step 1: 제품 이해 및 프롬프트 증강
- Step 2: 광고 시나리오 기획
- Step 3: 제어맵 생성 (Replicate API)
- [FIXED] Step 4: 키프레임 생성 (SDXL + IP-Adapter + ControlNet)
- 번역 API: 영어→한글 (디버깅용)
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import logging

# Common 모듈 import
from common.paths import TaskPaths
from common.redis_manager import RedisManager
from common.config import Config
from common.logger import TaskLogger

# Pipeline Steps
from pipeline.step0_agentic import Step0_Agentic_Preprocessing
from pipeline.step1_understanding import Step1_Understanding
from pipeline.step2_planning import Step2_Planning
from pipeline.step3_api import ControlMapGeneratorAPI

# NOTE:
# Step 4는 diffusers/transformers 로딩 비용이 커서 서버 기동 시 import 하면
# Flask reloader에서 매우 느려지거나 타임아웃/인터럽트로 보일 수 있습니다.
# 따라서 Step 4 관련 import는 엔드포인트 호출 시점에 지연 로딩합니다.

# ✅ 오프라인 모드 강제 비활성화
os.environ['TRANSFORMERS_OFFLINE'] = '0'
os.environ['HF_HUB_OFFLINE'] = '0'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'  # 선택사항

print(f"🔧 환경변수 설정:")
print(f"   - TRANSFORMERS_OFFLINE: {os.environ.get('TRANSFORMERS_OFFLINE')}")
print(f"   - HF_HUB_OFFLINE: {os.environ.get('HF_HUB_OFFLINE')}")


load_dotenv()

app = Flask(__name__)
CORS(app)
cfg = Config.load()
redis_mgr = RedisManager.from_env()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger(__name__)

# OpenAI 클라이언트 (번역용)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 파일 업로드 설정
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_TOTAL_SIZE = 50 * 1024 * 1024 
app.config['MAX_CONTENT_LENGTH'] = MAX_TOTAL_SIZE

# Temp 디렉토리
TEMP_DIR = "data/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== Step 0: 배경 제거 ====================
@app.route('/api/test/step0', methods=['POST'])
def test_step0_endpoint():
    try:
        if 'images' not in request.files:
            return jsonify({"error": "No images provided"}), 400
        
        files = request.files.getlist('images')
        prompt = request.form.get('prompt', '')

        if not files or files[0].filename == '':
            return jsonify({"error": "No files selected"}), 400

        task_id = f"test_ui_{uuid.uuid4().hex[:8]}"
        paths = TaskPaths.from_repo(task_id)
        paths.ensure_dirs()
        
        task_logger = TaskLogger(task_id, paths.run_log)
        task_logger.info(f"🧪 [Step 0] Started. Images: {len(files)}, Prompt: {prompt}")

        step0 = Step0_Agentic_Preprocessing()
        results = []

        for idx, file in enumerate(files, 1):
            if not allowed_file(file.filename): 
                continue
            
            ext = file.filename.rsplit('.', 1)[1].lower()
            input_path = paths.input_image(idx, ext)
            file.save(str(input_path))

            try:
                task_logger.info(f"Processing image {idx}: {file.filename}")
                output_path = step0.run(
                    task_id=task_id,
                    input_path=str(input_path),
                    output_dir=str(paths.temp_task_dir)
                )
                results.append({
                    "original_path": str(input_path.absolute()),
                    "processed_path": str(Path(output_path).absolute()),
                    "filename": file.filename
                })
            except Exception as e:
                task_logger.error(f"Image {idx} failed: {e}")
                results.append({"error": str(e), "filename": file.filename})

        return jsonify({
            "task_id": task_id,
            "status": "success",
            "results": results,
            "prompt": prompt
        })

    except Exception as e:
        logger.error(f"❌ Step 0 Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ==================== Step 1: 제품 이해 ====================
@app.route('/api/test/step1', methods=['POST'])
def test_step1_endpoint():
    try:
        data = request.json
        image_path = data.get('image_path')
        user_prompt = data.get('user_prompt', '')

        if not image_path:
            return jsonify({"error": "image_path is required"}), 400
        
        if not os.path.exists(image_path):
            return jsonify({"error": f"Image file not found at: {image_path}"}), 404

        step1 = Step1_Understanding()
        task_id = f"test_step1_{uuid.uuid4().hex[:8]}"
        
        result = step1.run(task_id, image_path, user_prompt)
        
        return jsonify({
            "status": "success",
            "analysis": result
        })

    except Exception as e:
        logger.error(f"❌ Step 1 Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ==================== Step 2: 기획 (Planning) ====================
@app.route('/api/test/step2', methods=['POST'])
def test_step2_endpoint():
    """
    POST /api/test/step2
    - 입력: image_path, analysis_data
    - 기능: GPT-4o 시나리오 기획 (Continuity 중심)
    """
    try:
        data = request.json
        image_path = data.get('image_path')
        analysis_data = data.get('analysis_data')

        if not image_path or not analysis_data:
            return jsonify({"error": "Missing required data"}), 400
        
        # Step 2 실행
        step2 = Step2_Planning()
        task_id = f"test_step2_{uuid.uuid4().hex[:8]}"
        
        scenario_result = step2.run(task_id, image_path, analysis_data)
        
        return jsonify({
            "status": "success",
            "scenario": scenario_result
        })

    except Exception as e:
        logger.error(f"❌ Step 2 Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ==================== Step 3: 제어맵 생성 ====================
@app.route('/api/test/step3', methods=['POST'])
def test_step3_endpoint():
    """
    POST /api/test/step3
    - 입력: {"image_path": "data/temp/.../product_processed.png"}
    - 출력: {"maps": {"mask_path": ..., "bbox_path": ..., "softedge_path": ..., "depth_path": ...}}
    - 기능: Replicate API로 제어맵 생성 (SoftEdge, Depth, Mask, BBox)
    """
    try:
        data = request.json
        image_path = data.get('image_path')

        # 입력 검증
        if not image_path:
            return jsonify({"error": "image_path is required"}), 400
        
        if not os.path.exists(image_path):
            return jsonify({"error": f"Image file not found at: {image_path}"}), 404

        # Task ID 생성 및 출력 디렉토리 설정
        task_id = f"test_step3_{uuid.uuid4().hex[:8]}"
        output_dir = os.path.join(TEMP_DIR, task_id, "step3")
        os.makedirs(output_dir, exist_ok=True)

        # Step 3 실행
        logger.info(f"🚀 [Step 3] Started for task: {task_id}")
        
        try:
            generator = ControlMapGeneratorAPI()
            maps = generator.run(image_path, output_dir)
            
            # 성공 카운트
            success_count = len(maps)
            logger.info(f"✅ [Step 3] Completed: {success_count}/4 maps generated")
            
            return jsonify({
                "status": "success",
                "task_id": task_id,
                "maps": maps,
                "success_count": success_count
            })
        
        except ValueError as ve:
            # API 토큰 에러
            logger.error(f"❌ [Step 3] API Token Error: {str(ve)}")
            return jsonify({
                "error": "REPLICATE_API_TOKEN is missing or invalid",
                "details": str(ve)
            }), 401
        
        except Exception as e:
            # 기타 에러
            logger.error(f"❌ [Step 3] Processing Error: {str(e)}")
            return jsonify({
                "error": "Step 3 processing failed",
                "details": str(e)
            }), 500

    except Exception as e:
        logger.error(f"❌ Step 3 Endpoint Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ==================== [FIXED] Step 4: 키프레임 생성 ====================
@app.route('/api/test/step4', methods=['POST'])
def test_step4_endpoint():
    """
    POST /api/test/step4
    - 입력: {
        "product_image": "data/temp/.../image_1_processed.png",
        "visual_dna": "...",           # Step 1 결과
        "scenario": {...},              # Step 2 결과 (3개 Scene)
        "control_maps": {...}           # Step 3 결과
      }
    - 출력: {
        "task_id": "test_step4_xxx",
        "keyframes": {
            "scene1_start": "data/temp/.../scene1_start.png",
            "scene1_end": "data/temp/.../scene1_end.png",
            ...  # 총 6개 (3 Scene × 2)
        }
      }
    - 기능: SDXL + IP-Adapter + Multi-ControlNet으로 키프레임 생성
    """
    try:
        data = request.json
        
        # 필수 입력 검증
        product_image = data.get('product_image')
        visual_dna = data.get('visual_dna')
        scenario = data.get('scenario')
        control_maps = data.get('control_maps')

        if not all([product_image, visual_dna, scenario, control_maps]):
            return jsonify({
                "error": "Missing required data",
                "required": ["product_image", "visual_dna", "scenario", "control_maps"]
            }), 400
        
        # 파일 존재 확인
        if not os.path.exists(product_image):
            return jsonify({"error": f"Product image not found: {product_image}"}), 404
        
        # Task ID 생성
        task_id = f"test_step4_{uuid.uuid4().hex[:8]}"
        output_dir = os.path.join(TEMP_DIR, task_id, "step4")
        os.makedirs(output_dir, exist_ok=True)

        logger.info(f"🚀 [Step 4] Started for task: {task_id}")
        logger.info(f"   - Product Image: {Path(product_image).name}")
        logger.info(f"   - Scenes: {len(scenario.get('scenes', []))}")

        # Step4는 heavy dependency(diffusers/transformers) 로딩이 필요하므로
        # 서버 기동 속도를 위해 요청 시점에 지연 import 합니다.
        try:
            from pipeline.step4_generation import get_step4_generator  # [FIXED] 싱글톤 getter 사용
        except Exception as import_err:
            logger.error(f"❌ [Step 4] Import Error: {str(import_err)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "error": "Step 4 dependencies are not available",
                "details": str(import_err)
            }), 500

        generator = get_step4_generator()
        
        # 키프레임 생성 (내부에서 자동으로 모델 로딩)
        keyframes = generator.generate_keyframes(
            product_image=product_image,
            visual_dna=visual_dna,
            scenario=scenario,
            control_maps=control_maps,
            output_dir=output_dir,
            num_inference_steps=30,
            guidance_scale=7.5,
            controlnet_scale=[0.5, 0.8],
            seed=42
        )
        
        logger.info(f"✅ [Step 4] Completed: {len(keyframes)}/6 keyframes generated")
        
        return jsonify({
            "status": "success",
            "task_id": task_id,
            "keyframes": keyframes,
            "count": len(keyframes)
        })
    
    except RuntimeError as re:
        # 모델 로딩 에러
        logger.error(f"❌ [Step 4] Model Loading Error: {str(re)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "error": "Model loading failed",
            "details": str(re)
        }), 500
    
    except Exception as e:
        # 기타 에러
        logger.error(f"❌ [Step 4] Processing Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "error": "Step 4 processing failed",
            "details": str(e)
        }), 500

# ==================== 번역 API (영어→한글) ====================
@app.route('/api/translate', methods=['POST'])
def translate_endpoint():
    """
    POST /api/translate
    - 입력: {"text": "English text"}
    - 출력: {"translation": "한글 번역"}
    - 용도: 디버깅용 (화면 표시만, Session State 저장 안 함)
    """
    try:
        data = request.json
        text = data.get('text', '')

        if not text:
            return jsonify({"error": "text is required"}), 400

        # GPT-4o로 번역 (간단하고 정확)
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # 비용 절감
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional translator. Translate the given English text to Korean naturally. Only output the translation, no explanations."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=500,
            temperature=0.3
        )

        translation = response.choices[0].message.content.strip()

        return jsonify({
            "status": "success",
            "translation": translation
        })

    except Exception as e:
        logger.error(f"❌ Translation Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ==================== Health Check ====================
@app.route('/health', methods=['GET'])
def health_check():
    """서버 상태 확인"""
    return jsonify({
        "status": "healthy",
        "endpoints": [
            "/api/test/step0",
            "/api/test/step1",
            "/api/test/step2",
            "/api/test/step3",
            "/api/test/step4",  # [NEW]
            "/api/translate"
        ]
    })

if __name__ == '__main__':
    print("🚀 Starting ADEASY_SHORTS API Server...")
    print("📍 Available endpoints:")
    print("   - POST /api/test/step0  (배경 제거)")
    print("   - POST /api/test/step1  (제품 이해)")
    print("   - POST /api/test/step2  (시나리오 기획)")
    print("   - POST /api/test/step3  (제어맵 생성)")
    print("   - POST /api/test/step4  (키프레임 생성) [NEW]")
    print("   - POST /api/translate   (번역)")
    print("   - GET  /health          (상태 확인)")
    app.run(host='0.0.0.0', port=5000, debug=True)
