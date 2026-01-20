# frontend/test_debug.py
import streamlit as st
import requests
from PIL import Image
import os
import json
import base64
from io import BytesIO

# ===== [CRITICAL] .env 파일 로드 =====
from dotenv import load_dotenv
load_dotenv()  # 반드시 맨 위에!
# ====================================

# 페이지 기본 설정
st.set_page_config(
    layout="wide", 
    page_title="ADEasy Shorts Project Debugger",
    page_icon="🎬"
)

API_BASE_URL = "http://localhost:5000"

# ✨ 1) 타이틀에 "Debugger" 추가
st.title("🎬 ADEasy Shorts Project Debugger")
st.caption("디버깅 및 테스트용 UI | Debugging & Testing Interface")

# ==========================================
# [Session State] 데이터 흐름 관리
# ==========================================
if 'step0_results' not in st.session_state:
    st.session_state['step0_results'] = []
if 'user_prompt' not in st.session_state:
    st.session_state['user_prompt'] = ""
if 'step1_analysis' not in st.session_state:
    st.session_state['step1_analysis'] = None
if 'step2_scenario' not in st.session_state:
    st.session_state['step2_scenario'] = None
if 'step3_maps' not in st.session_state:
    st.session_state['step3_maps'] = None
if 'step4_keyframes' not in st.session_state:  # [NEW] Step 4 결과 저장
    st.session_state['step4_keyframes'] = {}

# ==========================================
# [Helper Function] 번역 API 호출
# ==========================================
def translate_to_korean(text):
    """영어 텍스트를 한글로 번역 (디버깅용)"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/translate",
            json={"text": text},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get('translation', '번역 실패')
        else:
            return f"⚠️ 번역 오류: {response.text}"
    except Exception as e:
        return f"⚠️ 연결 오류: {str(e)}"

# ==========================================
# [Helper Function] 이미지 다운로드 버튼
# ==========================================
def get_image_download_link(image_path, filename="image.png"):
    """이미지 다운로드 버튼 생성"""
    try:
        with open(image_path, "rb") as file:
            img_bytes = file.read()
        
        # Base64 인코딩
        b64 = base64.b64encode(img_bytes).decode()
        
        # 다운로드 버튼 생성
        href = f'<a href="data:image/png;base64,{b64}" download="{filename}">📥 다운로드</a>'
        return href
    except Exception as e:
        return f"⚠️ 다운로드 실패: {str(e)}"

# ==========================================
# [Tabs] 탭 구성
# ==========================================
tabs = st.tabs([
    "🏠 Main Page",
    "Step 0: Preprocessing", 
    "Step 1: Understanding", 
    "Step 2: Planning", 
    "Step 3: Control Maps", 
    "Step 4: Keyframes",  # Step 4 탭 활성화
    "Step 5: Video Gen"
])

tab_main = tabs[0]
tab0 = tabs[1]
tab1 = tabs[2]
tab2 = tabs[3]
tab3 = tabs[4]
tab4 = tabs[5]  # Step 4 탭

# =========================================================
# [Tab Main] 프로젝트 소개
# =========================================================
with tab_main:
    st.markdown("### 🚀 AI Based Automated Advertising Video Generation Pipeline")
    st.markdown("""
    이 프로젝트는 **제품 이미지 1~4장**만으로 시나리오 기획부터 영상 생성, 편집까지 
    **전 과정을 AI가 자동으로 수행**하여 **15초 세로형 광고 영상**을 제작하는 솔루션입니다.
    
    - **입력**: 제품 사진 1~4장 (+ 선택적 텍스트 프롬프트)
    - **출력**: 15초 세로형 광고 영상 (1080×1920, 24fps)
    - **시간**: 15분 이내 (인간 대비 1,000배 단축)
    - **핵심 혁신**: Agentic Workflow (생성 → 평가 → 개선)
    """)
    
    st.divider()
    
    # ===== 1️⃣ 가로형 로드맵 (Step 0~9 확장) =====
    st.subheader("🗺️ 전체 파이프라인 로드맵 (Full Pipeline)")
    
    st.markdown("""
    <style>
        .roadmap-container { 
            display: flex; 
            flex-wrap: wrap; 
            justify-content: center; 
            gap: 10px; 
            padding: 20px; 
            background-color: #262730; 
            border-radius: 15px; 
            margin-bottom: 40px; 
        }
        .step-card { 
            background: linear-gradient(145deg, #2e3039, #1f2026); 
            border: 1px solid #4e5058; 
            border-radius: 10px; 
            padding: 12px; 
            width: 110px; 
            text-align: center; 
            transition: transform 0.2s;
        }
        .step-card:hover {
            transform: scale(1.05);
        }
        .step-title { 
            font-weight: bold; 
            font-size: 0.95em; 
            color: #ff4b4b; 
            margin-bottom: 5px; 
        }
        .step-desc { 
            font-size: 0.75em; 
            color: #fafafa; 
            line-height: 1.3;
        }
        .arrow { 
            display: flex; 
            align-items: center; 
            font-size: 1.3em; 
            color: #666; 
            font-weight: bold; 
        }
    </style>
    <div class="roadmap-container">
        <div class="step-card"><div class="step-title">Step 0</div><div class="step-desc">배경 제거</div></div>
        <div class="arrow">➜</div>
        <div class="step-card"><div class="step-title">Step 1</div><div class="step-desc">제품 이해</div></div>
        <div class="arrow">➜</div>
        <div class="step-card"><div class="step-title">Step 2</div><div class="step-desc">시나리오 기획</div></div>
        <div class="arrow">➜</div>
        <div class="step-card"><div class="step-title">Step 3</div><div class="step-desc">제어맵 생성</div></div>
        <div class="arrow">➜</div>
        <div class="step-card"><div class="step-title">Step 4</div><div class="step-desc">키프레임 생성</div></div>
        <div class="arrow">➜</div>
        <div class="step-card"><div class="step-title">Step 5</div><div class="step-desc">비디오 생성</div></div>
        <div class="arrow">➜</div>
        <div class="step-card"><div class="step-title">Step 6-8</div><div class="step-desc">후처리 및 조립</div></div>
        <div class="arrow">➜</div>
        <div class="step-card"><div class="step-title">Step 9</div><div class="step-desc">품질 검증</div></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # ===== 2️⃣ 세로형 상세 카드 (Step 0~3) =====
    st.subheader("📚 단계별 상세 설명")
    st.caption("현재 구현 완료된 단계에 대한 기술 상세 정보")
    
    st.markdown("""
    <style>
        .detail-card {
            background: linear-gradient(135deg, #1a2332 0%, #2a3f5f 100%);
            border: 1px solid #3a5f7f;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .detail-card h3 {
            color: #4fc3f7;
            margin-bottom: 10px;
            font-size: 1.3em;
        }
        .detail-card h4 {
            color: #81c784;
            margin-top: 15px;
            margin-bottom: 8px;
            font-size: 1.05em;
        }
        .detail-card p, .detail-card ul {
            color: #e0e0e0;
            font-size: 0.9em;
            line-height: 1.6;
        }
        .detail-card ul {
            margin-left: 20px;
        }
        .detail-card .metric-box {
            background: rgba(79, 195, 247, 0.1);
            border-left: 3px solid #4fc3f7;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
        }
        .data-flow-arrow {
            text-align: center;
            font-size: 2em;
            color: #4fc3f7;
            margin: 20px 0;
        }
        .data-flow-box {
            background: linear-gradient(135deg, #1e3a5f 0%, #2e4a6f 100%);
            border: 2px dashed #4fc3f7;
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
        }
        .data-flow-box h4 {
            color: #ffeb3b;
            margin-bottom: 10px;
        }
        .data-flow-box ul {
            color: #e0e0e0;
            margin-left: 20px;
        }
        .data-flow-box p {
            color: #e0e0e0;
        }
    </style>
    
    <div class="data-flow-box">
        <h4>📥 입력 데이터 (Step 0로 전달)</h4>
        <ul>
            <li><strong>광고 대상 이미지</strong>: 제품 사진 1~4장 (JPG, PNG, WebP 지원)</li>
            <li><strong>사용자 프롬프트</strong>: 광고 요청사항 (예: "여름 느낌의 시원한 광고를 만들어줘")</li>
        </ul>
        <p><strong>📂 입력 경로:</strong> <code>data/inputs/{task_id}/</code></p>
    </div>
    
    <div class="data-flow-arrow">⬇️</div>
    
    <div class="detail-card">
        <h3>🔹 Step 0: Agentic Background Removal</h3>
        
        <h4>📌 역할 및 목적</h4>
        <p>제품 이미지에서 배경을 자동으로 제거하여 제품만 남긴 투명 배경 이미지(RGBA PNG)를 생성합니다. 
        SAM 2 모델이 제품을 정확히 인식하고, GPT-4o가 결과물을 평가하여 최고 품질의 누끼 이미지를 보장합니다.</p>
        
        <h4>🔧 핵심 로직</h4>
        <ul>
            <li><strong>Box Prompting 전략</strong>: 중앙 60% 영역을 박스로 지정하여 메인 객체 전체 포착</li>
            <li><strong>Agentic Workflow</strong>: 생성 → GPT-4o 평가 → 불합격 시 파라미터 자동 조정 후 재시도 (최대 3회)</li>
            <li><strong>품질 평가 기준</strong>: 배경 잔여물 감지, 제품 절단 여부, 엣지 품질</li>
        </ul>
        
        <h4>🎯 적용 기법</h4>
        <ul>
            <li>Meta SAM 2의 Box Prompting 기능 활용</li>
            <li>GPT-4o Vision을 품질 평가자(Quality Checker)로 활용</li>
            <li>재시도 루프: conf=[0.4, 0.25, 0.1], iou=[0.8, 0.7, 0.6]</li>
        </ul>
        
        <h4>🤖 사용 모델</h4>
        <ul>
            <li><strong>SAM 2 (Segment Anything Model 2)</strong> - Meta 2024</li>
            <li><strong>GPT-4o Vision</strong> - 품질 평가용</li>
        </ul>
        
        <div class="metric-box">
            <strong>📊 성능 지표</strong><br>
            • 처리 시간: 평균 8초 (2초×3회 시도 + 평가)<br>
            • VRAM: 2GB<br>
            • 정확도 (IoU): 0.88<br>
            • 출력: RGBA PNG + 마스크 PNG
        </div>
    </div>
    
    <div class="data-flow-arrow">⬇️</div>
    
    <div class="data-flow-box">
        <h4>📦 Step 0 → Step 1 전달 데이터</h4>
        <ul>
            <li><code>processed_path</code>: 배경 제거된 RGBA PNG 파일 경로</li>
            <li><code>user_prompt</code>: 사용자가 입력한 광고 요청사항</li>
            <li><code>original_path</code>: 원본 이미지 경로 (참고용)</li>
        </ul>
        <p><strong>💾 저장 위치:</strong> <code>st.session_state['step0_results']</code> (리스트)</p>
        <p><strong>🗂️ 파일 경로:</strong> <code>data/temp/{task_id}/product_processed.png</code></p>
    </div>
    
    <div class="detail-card">
        <h3>🔹 Step 1: Product Understanding & Prompt Augmentation</h3>
        
        <h4>📌 역할 및 목적</h4>
        <p>Step 0의 누끼 이미지와 사용자 요청을 바탕으로 GPT-4o Vision이 제품을 깊이 이해하고 분석합니다. 
        핵심 정보를 추출하여 <strong>영상 생성에 최적화된 전문 프롬프트(Augmented Video Prompt)</strong>, 
        <strong>제품의 고유한 시각적 특징(Visual DNA)</strong>, <strong>메인 컨셉과 무드</strong>를 생성합니다.</p>
        
        <h4>🔧 핵심 로직</h4>
        <ul>
            <li><strong>Visual DNA 추출</strong>: 색상, 질감, 형태 등 제품 고유 특징 분석</li>
            <li><strong>프롬프트 증강</strong>: 사용자 입력 "맛있게 해줘" → 전문 영어 프롬프트 자동 생성</li>
            <li><strong>무드 분석</strong>: 광고 톤앤매너 결정 (Cinematic, Energetic, Luxury 등)</li>
        </ul>
        
        <h4>🎯 적용 기법</h4>
        <ul>
            <li>멀티모달 통합: 이미지 분석 + 텍스트 생성 한 번에 처리</li>
            <li>프롬프트 엔지니어링: Runway/Sora 스타일 전문 프롬프트 생성</li>
            <li>컨텍스트 증강: 사용자 요청 + 제품 특성 결합</li>
        </ul>
        
        <h4>🤖 사용 모델</h4>
        <ul>
            <li><strong>GPT-4o Vision</strong> - OpenAI 멀티모달 모델</li>
        </ul>
        
        <div class="metric-box">
            <strong>📊 성능 지표</strong><br>
            • 처리 시간: 평균 5초<br>
            • API 비용: $0.01/요청<br>
            • 정확도: 0.95<br>
            • 출력: JSON (augmented_video_prompt, visual_dna, mood_atmosphere, main_object)
        </div>
    </div>
    
    <div class="data-flow-arrow">⬇️</div>
    
    <div class="data-flow-box">
        <h4>📦 Step 1 → Step 2 전달 데이터</h4>
        <ul>
            <li><code>augmented_video_prompt</code>: 영상 생성 모델용 전문 영어 프롬프트</li>
            <li><code>visual_dna</code>: 제품의 고유한 시각적 특징 (일관성 유지용)</li>
            <li><code>main_object</code>: 제품 카테고리 (예: Hamburger, T-Shirt)</li>
            <li><code>mood_atmosphere</code>: 광고 무드 (예: Cinematic, Fresh)</li>
            <li><code>ad_keywords</code>: 광고 키워드 리스트</li>
        </ul>
        <p><strong>💾 저장 위치:</strong> <code>st.session_state['step1_analysis']</code> (딕셔너리)</p>
        <p><strong>🗂️ 파일 경로:</strong> <code>data/temp/{task_id}/step1_analysis.json</code></p>
    </div>
    
    <div class="detail-card">
        <h3>🔹 Step 2: Creative Planning & Continuity Design</h3>
        
        <h4>📌 역할 및 목적</h4>
        <p>Step 1의 분석 결과를 바탕으로 AI 감독이 3개의 Scene으로 구성된 15초 광고 시나리오를 자동 기획합니다. 
        각 Scene 간 <strong>시각적 연속성(Visual Continuity)</strong>을 보장하여 끊김 없는 스토리텔링과 프로급 영상 품질을 구현합니다.</p>
        
        <h4>🔧 핵심 로직</h4>
        <ul>
            <li><strong>Adaptive Directing</strong>: 제품 카테고리(음식/패션/테크) 자동 감지 후 연출 전략 변경</li>
            <li><strong>Visual Continuity</strong>: Scene 1 끝 프레임 = Scene 2 시작 프레임 명시적 설계</li>
            <li><strong>3-Scene 구조</strong>: AIDA 프레임워크 (Attention → Interest → Desire → Action)</li>
        </ul>
        
        <h4>🎯 적용 기법</h4>
        <ul>
            <li>멀티모달 컨텍스트: Step 1 분석 + 원본 이미지 동시 활용</li>
            <li>프레임 연결 설계: Start Frame → End Frame → Transition 명시</li>
            <li>카메라 무브먼트: Zoom In/Out, Pan, Orbit, Static 자동 배정</li>
        </ul>
        
        <h4>🤖 사용 모델</h4>
        <ul>
            <li><strong>GPT-4o</strong> - 시나리오 기획 및 Continuity 설계</li>
        </ul>
        
        <div class="metric-box">
            <strong>📊 성능 지표</strong><br>
            • 처리 시간: 평균 4초<br>
            • API 비용: $0.01/요청<br>
            • 정확도: 0.95<br>
            • 출력: JSON (concept_title, product_category, scenes[3])
        </div>
    </div>
    
    <div class="data-flow-arrow">⬇️</div>
    
    <div class="data-flow-box">
        <h4>📦 Step 2 → Step 3 전달 데이터</h4>
        <ul>
            <li><code>scenes</code>: 3개 Scene 배열 (각 Scene의 description, camera_movement, continuity_plan 포함)</li>
            <li><code>concept_title</code>: 시나리오 제목</li>
            <li><code>product_category</code>: 제품 카테고리 (Food, Fashion, Tech 등)</li>
            <li><code>start_frame_description</code>: 각 Scene의 시작 프레임 설명</li>
            <li><code>end_frame_description</code>: 각 Scene의 끝 프레임 설명</li>
        </ul>
        <p><strong>💾 저장 위치:</strong> <code>st.session_state['step2_scenario']</code> (딕셔너리)</p>
        <p><strong>🗂️ 파일 경로:</strong> <code>data/temp/{task_id}/step2_scenario.json</code></p>
    </div>
    
    <div class="detail-card">
        <h3>🔹 Step 3: Control Maps Generation</h3>
        
        <h4>📌 역할 및 목적</h4>
        <p>영상 생성(Step 5)을 위한 <strong>4가지 가이드라인(제어맵)</strong>을 생성합니다. 
        Replicate API를 사용하여 VRAM 0GB로 고품질 제어맵을 확보합니다.</p>
        
        <h4>🔧 생성되는 제어맵 4종</h4>
        <ul>
            <li><strong>SoftEdge Map</strong>: 제품의 부드러운 윤곽선 (형태 유지, 텍스처 보존)</li>
            <li><strong>Depth Map</strong>: 제품의 입체감과 거리 정보 (3D 회전 시 필수)</li>
            <li><strong>Product Mask</strong>: 제품과 배경을 분리하는 마스크 (합성용)</li>
            <li><strong>BBox JSON</strong>: 제품 위치 정보 (x, y, width, height)</li>
        </ul>
        
        <h4>🤖 사용 기술</h4>
        <ul>
            <li><strong>Replicate API</strong> - ControlNet Preprocessors</li>
            <li><strong>로컬 처리</strong> - Mask & BBox 추출</li>
        </ul>
        
        <div class="metric-box">
            <strong>📊 성능 지표</strong><br>
            • 처리 시간: 약 120초<br>
            • VRAM: 0GB (클라우드 API)<br>
            • 비용: ~$0.05/1회 요청<br>
            • 출력: 4개 파일 (PNG×3 + JSON×1)
        </div>
    </div>
    
    <div class="data-flow-arrow">⬇️</div>
    
    <div class="data-flow-box">
        <h4>📦 Step 3 → Step 4 전달 데이터</h4>
        <ul>
            <li><code>softedge_path</code>: SoftEdge Map 파일 경로</li>
            <li><code>depth_path</code>: Depth Map 파일 경로</li>
            <li><code>mask_path</code>: Product Mask 파일 경로</li>
            <li><code>bbox_path</code>: BBox JSON 파일 경로</li>
        </ul>
        <p><strong>💾 저장 위치:</strong> <code>st.session_state['step3_maps']</code> (딕셔너리)</p>
        <p><strong>🗂️ 파일 경로:</strong> <code>data/temp/{task_id}/step3_*.png</code></p>
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# [Tab 0] Step 0: 입력 및 배경 제거
# =========================================================
with tab0:
    st.header("Step 0: Input & Agentic Background Removal")
    
    st.markdown("""
    제품 이미지에서 배경을 자동으로 제거하여 제품만 남긴 투명 배경 이미지(PNG)를 생성합니다. SAM 2 모델이 제품을 인식하고, GPT-4o가 결과물을 평가하여 최고 품질의 누끼 이미지를 보장합니다.
    
    **💡 왜 필요한가요?**
    - 깔끔한 배경 제거로 제품이 돋보이게 만듭니다
    - 향후 영상 생성 시 배경을 자유롭게 합성할 수 있습니다
    - 광고 품질을 높이는 첫 단계입니다
    """)
    
    st.divider()
    
    with st.container(border=True):
        st.subheader("📤 입력 데이터")
        col_input, col_prompt = st.columns([1, 1])
        
        with col_input:
            st.markdown("##### 1️⃣ 제품 이미지 업로드 **[필수]**")
            uploaded_files = st.file_uploader(
                "최대 4장까지 업로드 가능", 
                type=['jpg', 'jpeg', 'png', 'webp'], 
                accept_multiple_files=True, 
                key="step0_uploader",
                help="배경이 있는 제품 이미지를 업로드하세요. AI가 자동으로 배경을 제거합니다."
            )
        
        with col_prompt:
            st.markdown("##### 2️⃣ 광고 요청사항 **[필수]**")
            prompt_input = st.text_area(
                "어떤 광고를 만들고 싶으신가요?",
                value=st.session_state['user_prompt'],
                key="prompt_input_widget",
                height=120,
                placeholder="예시: 여름 느낌의 시원한 광고를 만들어줘",
                help="사용자의 요청을 자유롭게 입력하세요. AI가 전문 프롬프트로 변환합니다."
            )
    
    st.divider()
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🚀 Start Pipeline (Run Step 0)", type="primary", use_container_width=True):
            if not uploaded_files:
                st.error("⚠️ **제품 이미지를 업로드해주세요!** (필수 입력)")
            elif not prompt_input or prompt_input.strip() == "":
                st.error("⚠️ **광고 요청사항을 입력해주세요!** (필수 입력)")
            else:
                st.session_state['user_prompt'] = prompt_input
                
                with st.spinner("🤖 Agentic AI (SAM 2) Processing..."):
                    files = [('images', (file.name, file.getvalue(), file.type)) for file in uploaded_files]
                    data = {'prompt': prompt_input}
                    try:
                        response = requests.post(f"{API_BASE_URL}/api/test/step0", files=files, data=data)
                        if response.status_code == 200:
                            st.session_state['step0_results'] = response.json()['results']
                            st.success("✅ Step 0 완료! 아래에서 결과를 확인하고 Step 1 탭으로 이동하세요.")
                        else: 
                            st.error(f"❌ Server Error: {response.text}")
                    except Exception as e: 
                        st.error(f"❌ Connection Error: {e}")
    
    if st.session_state['step0_results']:
        st.divider()
        st.subheader("👀 처리 결과")
        
        for idx, item in enumerate(st.session_state['step0_results'], 1):
            if "error" in item: 
                st.error(f"이미지 {idx} 처리 실패: {item['error']}")
                continue
            
            with st.container(border=True):
                st.markdown(f"**📷 이미지 {idx}: {item.get('filename', 'Unknown')}**")
                c1, c2 = st.columns(2)
                
                with c1: 
                    st.markdown("**원본 (Original)**")
                    try: 
                        st.image(item['original_path'], use_container_width=True)
                    except: 
                        st.warning("이미지 로드 실패")
                
                with c2: 
                    st.markdown("**배경 제거 결과 (No Background)**")
                    try: 
                        st.image(item['processed_path'], use_container_width=True)
                        
                        if os.path.exists(item['processed_path']):
                            with open(item['processed_path'], "rb") as file:
                                st.download_button(
                                    label="📥 배경 제거 이미지 다운로드",
                                    data=file,
                                    file_name=f"no_bg_{item.get('filename', 'image.png')}",
                                    mime="image/png",
                                    use_container_width=True
                                )
                    except: 
                        st.warning("이미지 로드 실패")

# =========================================================
# [Tab 1] Step 1: 제품 이해
# =========================================================
with tab1:
    st.header("Step 1: Product Understanding & Prompt Augmentation")
        
    st.markdown("""
    Step 0에서 배경이 제거된 제품 이미지와 사용자의 광고 요청사항을 바탕으로, GPT-4o Vision이 제품을 깊이 이해하고 분석합니다.  
    핵심 정보를 추출하여 **영상 생성에 최적화된 전문 프롬프트(Augmented Video Prompt)**, **제품의 고유한 시각적 특징(Visual DNA)**, 
    **메인 컨셉과 무드**를 생성합니다.

    **💡 왜 필요한가요?** 
    - **Step 2 시나리오 기획**에 필요한 콘셉트와 프롬프트를 구체화합니다
    - AI 영상 생성 모델(Runway, Sora, LTX-Video 등)이 이해할 수 있는 형태로 변환합니다
    """)
    
    st.divider()
    
    if not st.session_state['step0_results']:
        st.warning("⚠️ Step 0을 먼저 실행해주세요.")
    else:
        target_info = st.session_state['step0_results'][0]
        
        st.success(f"✅ Step 0 데이터 로드 완료 (파일: {target_info.get('filename', 'Unknown')})")
        
        col_img, col_btn = st.columns([1, 2])
        with col_img:
            if os.path.exists(target_info['processed_path']):
                st.image(target_info['processed_path'], caption="분석 대상 이미지", use_container_width=True)
            else:
                st.error("이미지 파일을 찾을 수 없습니다.")

        with col_btn:
            with st.container(border=True):
                st.markdown("**📝 사용자 요청사항**")
                st.info(st.session_state['user_prompt'] if st.session_state['user_prompt'] else "요청사항 없음 (자동 분석)")
            
            if st.button("✨ Run Step 1 (Analyze)", type="primary", use_container_width=True):
                with st.spinner("🧠 GPT-4o Vision 분석 중..."):
                    try:
                        payload = {
                            "image_path": target_info['processed_path'], 
                            "user_prompt": st.session_state['user_prompt']
                        }
                        response = requests.post(f"{API_BASE_URL}/api/test/step1", json=payload)
                        
                        if response.status_code == 200:
                            st.session_state['step1_analysis'] = response.json()['analysis']
                            st.success("✅ Step 1 분석 완료!")
                        else:
                            st.error(f"❌ Error: {response.text}")
                    except Exception as e: 
                        st.error(f"❌ Connection Error: {e}")
        
        if st.session_state['step1_analysis']:
            data = st.session_state['step1_analysis']
            st.divider()
            
            with st.container(border=True):
                st.markdown("#### 1️⃣ Augmented Video Prompt (English)")
                st.caption("💡 AI 영상 생성 모델(Runway, Sora 등)이 이해할 수 있도록 변환된 전문 시네마틱 프롬프트")
                st.code(data.get('augmented_video_prompt', 'N/A'), language="text")
                
                with st.expander("🇰🇷 한글 번역 보기 (참고용, 디버깅 전용)"):
                    if st.button("번역하기", key="translate_prompt"):
                        with st.spinner("번역 중..."):
                            translation = translate_to_korean(data.get('augmented_video_prompt', ''))
                            st.info(translation)
            
            with st.container(border=True):
                st.markdown("#### 2️⃣ Main Concept & Mood")
                st.caption("💡 제품의 핵심 컨셉과 광고 분위기를 정의합니다")
                col_concept, col_mood = st.columns(2)
                with col_concept:
                    st.metric("Main Concept", data.get('main_object', 'N/A'))
                with col_mood:
                    st.metric("Mood", data.get('mood_atmosphere', 'N/A'))
            
            with st.container(border=True):
                st.markdown("#### 3️⃣ Visual DNA")
                st.caption("💡 제품의 고유한 시각적 특징으로, 향후 이미지 생성 시 일관성 유지를 위해 사용됩니다")
                st.info(data.get('visual_dna', 'N/A'))
                
                with st.expander("🇰🇷 한글 번역 보기 (참고용, 디버깅 전용)"):
                    if st.button("번역하기", key="translate_dna"):
                        with st.spinner("번역 중..."):
                            translation = translate_to_korean(data.get('visual_dna', ''))
                            st.info(translation)
            
            with st.expander("📄 Raw Data (JSON)"):
                st.json(data)

# =========================================================
# [Tab 2] Step 2: 기획
# =========================================================
with tab2:
    st.header("Step 2: Creative Planning & Continuity Design")
    
    st.markdown("""
    Step 1에서 분석된 제품 정보(Main Concept, Mood, Visual DNA)를 바탕으로, AI 감독이 3개의 Scene으로 구성된 15초 광고 시나리오를 자동 기획합니다.  
    각 Scene 간 **시각적 연속성(Visual Continuity)** 을 보장하여, 끊김 없는 스토리텔링과 프로급 영상 품질을 구현합니다.
    
    **💡 왜 필요한가요?** 
    - **Scene 1(Intro) → Scene 2(Body) → Scene 3(Outro)** 의 논리적 흐름 구성
    - 각 Scene의 **Start Frame**과 **End Frame**을 명확히 정의하여 Step 4/5의 영상 생성에 활용
    - 제품 카테고리에 맞는 촬영 기법(카메라 무브먼트, 조명, 구도)을 자동 적용
    """)
    
    st.divider()
    
    if not st.session_state['step1_analysis']:
        st.warning("⚠️ Step 1을 먼저 완료해주세요.")
    else:
        st.success("✅ Step 1 데이터 로드 완료")
        
        analysis_data = st.session_state['step1_analysis']
        target_path = st.session_state['step0_results'][0]['processed_path']

        st.divider()
        st.subheader("📋 Step 1에서 전달된 기획 재료")
        
        col_img_large, col_data_cards = st.columns([1, 2])
        
        with col_img_large:
            with st.container(border=True):
                st.markdown("##### 🖼️ 시나리오 기획 대상 이미지")
                st.caption("💡 배경이 제거된 제품 이미지 (Step 0 산출물)")
                if os.path.exists(target_path):
                    st.image(target_path, use_container_width=True, caption="누끼 딴 제품 이미지")
                else:
                    st.error("이미지를 찾을 수 없습니다.")
        
        with col_data_cards:
            with st.container(border=True):
                st.markdown("##### 🎯 Main Concept & Mood")
                st.caption("💡 제품의 핵심 컨셉과 광고 분위기 (시나리오 톤 결정)")
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("제품", analysis_data.get('main_object', 'N/A'))
                with c2:
                    st.metric("무드", analysis_data.get('mood_atmosphere', 'N/A'))
            
            with st.container(border=True):
                st.markdown("##### 🧬 Visual DNA (제품 특징)")
                st.caption("💡 제품의 고유한 시각적 DNA (색상, 질감, 형태 등)")
                visual_dna = analysis_data.get('visual_dna', 'N/A')
                visual_dna_short = visual_dna[:100] + "..." if len(visual_dna) > 100 else visual_dna
                st.caption(visual_dna_short)
                with st.expander("전체 보기"):
                    st.info(visual_dna)
            
            with st.container(border=True):
                st.markdown("##### ✨ Augmented Video Prompt")
                st.caption("💡 영상 생성 모델용 전문 프롬프트 (Scene별 적용)")
                aug_prompt = analysis_data.get('augmented_video_prompt', 'N/A')
                aug_prompt_short = aug_prompt[:100] + "..." if len(aug_prompt) > 100 else aug_prompt
                st.caption(aug_prompt_short)
                with st.expander("전체 보기"):
                    st.code(aug_prompt, language="text")
            
            with st.container(border=True):
                st.markdown("##### 📝 사용자 요청사항")
                st.caption("💡 사용자가 입력한 광고 방향성 (Step 0 입력)")
                st.info(st.session_state['user_prompt'] if st.session_state['user_prompt'] else "요청사항 없음")

        st.divider()
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if st.button("📝 Run Step 2 (Generate Scenario)", type="primary", use_container_width=True):
                with st.spinner("🎬 AI 감독이 시나리오 작성 중... (Continuity Check)"):
                    try:
                        payload = {
                            "image_path": target_path, 
                            "analysis_data": analysis_data,
                            "user_prompt": st.session_state['user_prompt']
                        }
                        response = requests.post(f"{API_BASE_URL}/api/test/step2", json=payload)
                        
                        if response.status_code == 200:
                            st.session_state['step2_scenario'] = response.json()['scenario']
                            st.success("✅ 기획 완료!")
                        else: 
                            st.error(f"❌ Error: {response.text}")
                    except Exception as e: 
                        st.error(f"❌ Connection Error: {e}")

        if st.session_state['step2_scenario']:
            scenario = st.session_state['step2_scenario']
            st.divider()
            st.subheader(f"🎬 Scenario: {scenario.get('concept_title')}")
            st.caption(f"**Category:** {scenario.get('product_category')} | **Target:** {scenario.get('target_audience')}")
            
            scenes = scenario.get('scenes', [])
            cols = st.columns(3)
            for idx, scene in enumerate(scenes):
                with cols[idx]:
                    with st.container(border=True):
                        st.markdown(f"### Scene {scene['scene_id']}: {scene['role']}")
                        st.caption(f"🎥 {scene.get('camera_movement')}")
                        st.divider()
                        
                        st.markdown("**📖 Description (English):**")
                        st.caption("💡 Scene 설명 (영상 생성 모델용)")
                        description_en = scene.get('description', 'N/A')
                        st.info(description_en)
                        
                        with st.expander("🇰🇷 한글 번역 보기 (참고용)"):
                            if st.button(f"번역하기 (Scene {scene['scene_id']})", key=f"translate_scene_{scene['scene_id']}"):
                                with st.spinner("번역 중..."):
                                    translation_kr = translate_to_korean(description_en)
                                    st.success(translation_kr)
                        
                        with st.expander("🔗 Frame-to-Frame Connection (Step 4/5용)"):
                            st.caption("💡 각 Scene의 시작/끝 프레임 정보 (영상 생성 시 활용)")
                            
                            st.markdown("**🎬 Start Frame:**")
                            st.caption(scene.get('start_frame_description', 'N/A'))
                            
                            st.markdown("**🎬 End Frame:**")
                            st.caption(scene.get('end_frame_description', 'N/A'))
                            
                            st.markdown("**➡️ Transition:**")
                            st.caption(scene.get('transition_to_next', 'N/A'))
                        
                        st.markdown("**🔗 Continuity:**")
                        st.caption("💡 이전 Scene과의 연결 방식")
                        st.warning(f"{scene.get('continuity_plan')}")
            
            with st.expander("📄 Raw Scenario JSON"): 
                st.json(scenario)

# =========================================================
# [Tab 3] Step 3: 제어맵 생성
# =========================================================
with tab3:
    st.header("Step 3: Control Maps Generation (Replicate API)")
    
    st.markdown("""
    영상 생성(Step 5)을 위한 **4가지 가이드라인(제어맵)** 을 생성합니다.  
    Replicate API를 사용하여 **VRAM 0GB**로 고품질 제어맵을 확보합니다.
    
    **💡 생성되는 제어맵 4종**  
    1. **SoftEdge Map** : 제품의 부드러운 윤곽선 (형태 유지, 텍스처 보존)  
    2. **Depth Map** : 제품의 입체감과 거리 정보 (3D 회전 시 필수)  
    3. **Product Mask** : 제품과 배경을 분리하는 마스크 (합성용)  
    4. **BBox JSON** : 제품 위치 정보 (x, y, width, height)
    """)
    
    st.divider()

    # ===== Step 0 데이터 확인 =====
    if not st.session_state['step0_results']:
        st.error("⚠️ **Step 0을 먼저 실행해주세요!**")
        st.info("💡 Step 0에서 배경이 제거된 제품 이미지가 필요합니다.")
        st.stop()
    
    # ===== 입력 이미지 및 실행 버튼 =====
    target_info = st.session_state['step0_results'][0]
    target_path = target_info['processed_path']
    
    col_input_img, col_btn_execute = st.columns([1, 2])
    
    with col_input_img:
        with st.container(border=True):
            st.markdown("##### 📥 입력 이미지 (Step 0 산출물)")
            if os.path.exists(target_path):
                st.image(target_path, caption="배경 제거된 제품 이미지", use_container_width=True)
            else:
                st.error("❌ 이미지 파일을 찾을 수 없습니다.")
    
    with col_btn_execute:
        with st.container(border=True):
            st.markdown("##### ⚙️ 제어맵 생성 설정")
            st.caption("💡 Replicate API를 호출하여 제어맵을 생성합니다.")
            
            # API 키 확인
            api_key_status = os.getenv('REPLICATE_API_TOKEN')
            if api_key_status:
                st.success("✅ Replicate API 키가 설정되어 있습니다.")
            else:
                st.error("❌ **REPLICATE_API_TOKEN 환경변수가 필요합니다!**")
                st.info("💡 `.env` 파일에 `REPLICATE_API_TOKEN=your_token` 추가 필요")
            
            st.markdown("---")
            st.markdown("**📊 예상 처리 시간:** 약 120초")
            st.markdown("**💾 VRAM 사용량:** 0GB (클라우드 API)")
            st.markdown("**💰 예상 비용:** ~$0.05/1회 요청")
            
            st.markdown("---")
            
            # 실행 버튼
            if st.button(
                "✨ Run Step 3 (Generate Control Maps)", 
                type="primary", 
                use_container_width=True,
                disabled=(not api_key_status)
            ):
                with st.spinner("🔄 Replicate API 호출 중... (SoftEdge, Depth, Mask 생성)"):
                    try:
                        # API 호출
                        payload = {"image_path": target_path}
                        response = requests.post(
                            f"{API_BASE_URL}/api/test/step3", 
                            json=payload,
                            timeout=240  # 타임아웃 240초
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            maps = result.get('maps', {})
                            st.session_state['step3_maps'] = maps
                            
                            # 성공 카운트
                            success_count = result.get('success_count', 0)
                            
                            if success_count == 4:
                                st.success(f"✅ **제어맵 생성 완료!** (4/4 성공)")
                            elif success_count >= 2:
                                st.warning(f"⚠️ **일부 성공** ({success_count}/4)")
                                st.info("💡 Mask와 BBox는 로컬 생성이라 항상 성공합니다. SoftEdge/Depth는 API 호출이 필요합니다.")
                            else:
                                st.error(f"❌ **생성 실패** ({success_count}/4)")
                        else:
                            error_data = response.json()
                            st.error(f"❌ **서버 오류:** {error_data.get('error', response.text)}")
                            
                            if response.status_code == 401:
                                st.info("💡 **해결 방법**: `.env` 파일에 올바른 `REPLICATE_API_TOKEN`을 설정하고 Backend를 재시작하세요.")
                    
                    except requests.exceptions.Timeout:
                        st.error("❌ **타임아웃:** API 응답 시간 초과 (240초)")
                    except Exception as e:
                        st.error(f"❌ **연결 실패:** {str(e)}")
    
    # ===== 결과 표시 =====
    if st.session_state['step3_maps']:
        st.divider()
        st.subheader("👀 생성된 제어맵 결과")
        
        maps = st.session_state['step3_maps']
        
        # 4개 이미지 그리드
        cols = st.columns(4)
        
        map_info = [
            ("SoftEdge Map", "softedge_path", "🖼️ 형태 가이드", "softedge.png"),
            ("Depth Map", "depth_path", "🌐 입체감 가이드", "depth.png"),
            ("Product Mask", "mask_path", "🎭 영역 분리", "mask.png"),
            ("BBox JSON", "bbox_path", "📐 위치 정보", "bbox.json")
        ]
        
        for idx, (title, key, desc, filename) in enumerate(map_info):
            with cols[idx]:
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    st.caption(desc)
                    
                    if key in maps and maps[key]:
                        path = maps[key]
                        
                        if key == "bbox_path":
                            # BBox는 JSON 표시
                            try:
                                with open(path, 'r') as f:
                                    bbox = json.load(f)
                                st.json(bbox)
                                
                                # 다운로드 버튼
                                with open(path, 'r') as f:
                                    st.download_button(
                                        "📥 다운로드",
                                        data=f.read(),
                                        file_name=filename,
                                        mime="application/json",
                                        use_container_width=True,
                                        key=f"download_{key}"
                                    )
                            except:
                                st.error("JSON 로드 실패")
                        else:
                            # 이미지 표시
                            try:
                                st.image(path, use_container_width=True)
                                
                                # 다운로드 버튼
                                with open(path, "rb") as f:
                                    st.download_button(
                                        "📥 다운로드",
                                        data=f,
                                        file_name=filename,
                                        mime="image/png",
                                        use_container_width=True,
                                        key=f"download_{key}"
                                    )
                            except:
                                st.error("이미지 로드 실패")
                    else:
                        st.error("❌ 생성 실패")
        
        # Raw JSON (디버깅용)
        with st.expander("📄 Raw Output JSON (디버깅용)"):
            st.json(maps)

# =========================================================
# [Tab 4] Step 4: 키프레임 생성 ⭐ NEW!
# =========================================================
with tab4:
    st.header("Step 4: Keyframe Generation (SDXL + ControlNet + IP-Adapter)")
    
    st.markdown("""
    Step 2의 **Scene별 시나리오**와 Step 3의 **제어맵**을 활용하여 각 Scene의 **Start Frame**과 **End Frame**을 생성합니다.  
    **SDXL Inpaint + ControlNet (SoftEdge, Depth) + IP-Adapter**를 사용하여 **제품 일관성**을 보장하고, 
    **시각적 연속성(Visual Continuity)** 을 유지합니다.
    
    **💡 생성되는 키프레임**  
    - **Scene 1**: Start Frame + End Frame (총 2장)  
    - **Scene 2**: Start Frame + End Frame (총 2장)  
    - **Scene 3**: Start Frame + End Frame (총 2장)  
    - **전체**: 6장의 키프레임 (704×1280, PNG)
    
    **💡 기술 스택**  
    - **SDXL Base 1.0** + **VAE Fix (fp16)**: 고품질 이미지 생성  
    - **Multi-ControlNet**: SoftEdge + Depth 동시 적용  
    - **IP-Adapter**: 제품 이미지 일관성 유지 (제품 색상, 질감 보존)  
    - **완전 로컬 실행**: L4 24GB GPU에서 실행 (VRAM ~14GB)
    """)
    
    st.divider()

    # ===== Step 0~3 데이터 확인 =====
    if not st.session_state['step0_results']:
        st.error("⚠️ **Step 0을 먼저 실행해주세요!**")
        st.stop()
    
    if not st.session_state['step1_analysis']:
        st.error("⚠️ **Step 1을 먼저 실행해주세요!**")
        st.stop()
    
    if not st.session_state['step2_scenario']:
        st.error("⚠️ **Step 2를 먼저 실행해주세요!**")
        st.stop()
    
    if not st.session_state['step3_maps']:
        st.error("⚠️ **Step 3을 먼저 실행해주세요!**")
        st.stop()
    
    # ===== 데이터 로드 =====
    product_image = st.session_state['step0_results'][0]['processed_path']
    visual_dna = st.session_state['step1_analysis'].get('visual_dna', '')
    scenario = st.session_state['step2_scenario']
    control_maps = st.session_state['step3_maps']
    
    st.success("✅ Step 0~3 데이터 로드 완료!")
    
    # ===== 입력 데이터 시각화 =====
    st.divider()
    st.subheader("📋 Step 4 입력 데이터 확인")
    
    with st.expander("🖼️ 제품 이미지 (IP-Adapter 입력)", expanded=False):
        if os.path.exists(product_image):
            st.image(product_image, caption="제품 누끼 이미지 (색상 일관성 유지용)", width=300)
        else:
            st.error("❌ 제품 이미지를 찾을 수 없습니다.")
    
    with st.expander("🧬 Visual DNA (제품 특징)", expanded=False):
        st.info(visual_dna if visual_dna else "N/A")
    
    with st.expander("🎬 Scene 정보 (총 3개)", expanded=True):
        scenes = scenario.get('scenes', [])
        for idx, scene in enumerate(scenes):
            st.markdown(f"**Scene {scene['scene_id']}: {scene['role']}**")
            st.caption(f"📖 {scene.get('description', 'N/A')}")
            st.caption(f"🎥 Camera: {scene.get('camera_movement', 'N/A')}")
            st.divider()
    
    with st.expander("🗺️ 제어맵 (ControlNet 입력)", expanded=False):
        cols = st.columns(3)
        
        if 'softedge_path' in control_maps and control_maps['softedge_path']:
            with cols[0]:
                st.markdown("**SoftEdge Map**")
                try:
                    st.image(control_maps['softedge_path'], use_container_width=True)
                except:
                    st.error("이미지 로드 실패")
        
        if 'depth_path' in control_maps and control_maps['depth_path']:
            with cols[1]:
                st.markdown("**Depth Map**")
                try:
                    st.image(control_maps['depth_path'], use_container_width=True)
                except:
                    st.error("이미지 로드 실패")
        
        if 'mask_path' in control_maps and control_maps['mask_path']:
            with cols[2]:
                st.markdown("**Product Mask**")
                try:
                    st.image(control_maps['mask_path'], use_container_width=True)
                except:
                    st.error("이미지 로드 실패")
    
    # ===== 실행 버튼 =====
    st.divider()
    st.subheader("⚙️ Step 4 실행")
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        with st.container(border=True):
            st.markdown("**📊 예상 처리 시간**")
            st.caption("• 모델 로딩: 약 30초 (최초 1회만)")
            st.caption("• Scene당 생성: 약 40초 (Start + End Frame)")
            st.caption("• 전체 예상 시간: **약 2~3분** (3 Scene × 2 Frame)")
            
            st.markdown("**💾 VRAM 사용량**")
            st.caption("• 약 14GB (L4 24GB 권장)")
            
            st.markdown("**💰 비용**")
            st.caption("• 완전 무료 (로컬 실행)")
            
            st.divider()
            
            if st.button(
                "✨ Run Step 4 (Generate Keyframes)", 
                type="primary", 
                use_container_width=True
            ):
                with st.spinner("🎨 SDXL 모델 로딩 중... (최초 1회 30초 소요)"):
                    try:
                        # 페이로드 구성
                        payload = {
                            "product_image": product_image,
                            "visual_dna": visual_dna,
                            "scenario": scenario,
                            "control_maps": control_maps
                        }
                        
                        # API 호출
                        response = requests.post(
                            f"{API_BASE_URL}/api/test/step4",
                            json=payload,
                            timeout=300  # 5분 타임아웃
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            keyframes = result.get('keyframes', {})
                            st.session_state['step4_keyframes'] = keyframes
                            
                            success_count = len(keyframes)
                            if success_count == 6:
                                st.success(f"✅ **키프레임 생성 완료!** (6/6 성공)")
                            else:
                                st.warning(f"⚠️ **일부 성공** ({success_count}/6)")
                        else:
                            error_data = response.json()
                            st.error(f"❌ **서버 오류:** {error_data.get('error', response.text)}")
                    
                    except requests.exceptions.Timeout:
                        st.error("❌ **타임아웃:** API 응답 시간 초과 (300초)")
                        st.info("💡 **해결 방법**: Backend 로그를 확인하고, VRAM 부족 여부를 체크하세요.")
                    except Exception as e:
                        st.error(f"❌ **연결 실패:** {str(e)}")
    
    # ===== 결과 표시 =====
    if st.session_state['step4_keyframes']:
        st.divider()
        st.subheader("👀 생성된 키프레임 결과")
        
        keyframes = st.session_state['step4_keyframes']
        
        # Scene별로 정리
        for scene_id in [1, 2, 3]:
            st.markdown(f"### 🎬 Scene {scene_id}")
            
            cols = st.columns(2)
            
            # Start Frame
            start_key = f"scene{scene_id}_start"
            if start_key in keyframes:
                with cols[0]:
                    with st.container(border=True):
                        st.markdown("**🎬 Start Frame**")
                        try:
                            st.image(keyframes[start_key], use_container_width=True)
                            
                            # 다운로드 버튼
                            with open(keyframes[start_key], "rb") as f:
                                st.download_button(
                                    "📥 다운로드",
                                    data=f,
                                    file_name=f"scene{scene_id}_start.png",
                                    mime="image/png",
                                    use_container_width=True,
                                    key=f"download_{start_key}"
                                )
                        except:
                            st.error("이미지 로드 실패")
            else:
                with cols[0]:
                    st.error("❌ Start Frame 생성 실패")
            
            # End Frame
            end_key = f"scene{scene_id}_end"
            if end_key in keyframes:
                with cols[1]:
                    with st.container(border=True):
                        st.markdown("**🎬 End Frame**")
                        try:
                            st.image(keyframes[end_key], use_container_width=True)
                            
                            # 다운로드 버튼
                            with open(keyframes[end_key], "rb") as f:
                                st.download_button(
                                    "📥 다운로드",
                                    data=f,
                                    file_name=f"scene{scene_id}_end.png",
                                    mime="image/png",
                                    use_container_width=True,
                                    key=f"download_{end_key}"
                                )
                        except:
                            st.error("이미지 로드 실패")
            else:
                with cols[1]:
                    st.error("❌ End Frame 생성 실패")
            
            st.divider()
        
        # Raw JSON (디버깅용)
        with st.expander("📄 Raw Output JSON (디버깅용)"):
            st.json(keyframes)

# =========================================================
# [Placeholder Tabs] Step 5
# =========================================================
with tabs[6]: 
    st.header("Step 5: Video Generation")
    st.warning("🚧 다음 단계 (구현 예정)")
    
    if st.session_state['step4_keyframes']:
        st.info("✅ Step 4 키프레임이 준비되었습니다. Step 5에서 영상을 생성할 수 있습니다.")