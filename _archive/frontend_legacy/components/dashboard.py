# frontend/components/dashboard.py
import streamlit as st

def render():
    st.markdown("### 🚀 AI Based Automated Advertising Video Generation Pipeline")
    st.markdown("""
    이 프로젝트는 **제품 이미지 1~4장**만으로 시나리오 기획부터 영상 생성, 편집까지 
    **전 과정을 AI가 자동으로 수행**하여 **15초 세로형 광고 영상**을 제작하는 솔루션입니다.
    
    - **입력** : 제품 사진 1~4장 (+ 선택적 텍스트 프롬프트)
    - **출력** : 15초 세로형 광고 영상 (1080×1920, 24fps)
    - **시간** : 15분 이내 (인간 대비 1,000배 단축)
    - **핵심 혁신** : Agentic Workflow (생성 → 평가 → 개선)
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
    
    # ===== 2️⃣ 세로형 상세 카드 =====
    st.subheader("📚 단계별 상세 설명")
    st.caption("현재 구현 완료된 단계에 대한 기술 상세 정보")
    
    # (CSS 스타일 및 카드 내용은 코드 길이상 생략하지 않고 원본 그대로 유지합니다)
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
        .detail-card h3 { color: #4fc3f7; margin-bottom: 10px; font-size: 1.3em; }
        .detail-card h4 { color: #81c784; margin-top: 15px; margin-bottom: 8px; font-size: 1.05em; }
        .detail-card p, .detail-card ul { color: #e0e0e0; font-size: 0.9em; line-height: 1.6; }
        .detail-card ul { margin-left: 20px; }
        .detail-card .metric-box {
            background: rgba(79, 195, 247, 0.1); border-left: 3px solid #4fc3f7;
            padding: 10px; margin: 10px 0; border-radius: 5px;
        }
        .data-flow-arrow { text-align: center; font-size: 2em; color: #4fc3f7; margin: 20px 0; }
        .data-flow-box {
            background: linear-gradient(135deg, #1e3a5f 0%, #2e4a6f 100%);
            border: 2px dashed #4fc3f7; border-radius: 10px; padding: 15px; margin: 15px 0;
        }
        .data-flow-box h4 { color: #ffeb3b; margin-bottom: 10px; }
        .data-flow-box ul { color: #e0e0e0; margin-left: 20px; }
        .data-flow-box p { color: #e0e0e0; }
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
        <p>제품 이미지에서 배경을 자동으로 제거하여 제품만 남긴 투명 배경 이미지(RGBA PNG)를 생성합니다.</p>
        <div class="metric-box">
            <strong>📊 성능 지표</strong><br>
            • 처리 시간: 평균 8초<br>• VRAM: 2GB<br>• 출력: RGBA PNG + 마스크 PNG
        </div>
    </div>
    
    <div class="data-flow-arrow">⬇️</div>
    
    <div class="data-flow-box">
        <h4>📦 Step 0 → Step 1 전달 데이터</h4>
        <ul>
            <li><code>processed_path</code>: 배경 제거된 RGBA PNG 파일 경로</li>
            <li><code>user_prompt</code>: 사용자 요청사항</li>
        </ul>
        <p><strong>💾 저장 위치:</strong> <code>st.session_state['step0_results']</code></p>
    </div>

    <div class="detail-card">
        <h3>🔹 Step 1: Product Understanding</h3>
        <h4>📌 역할 및 목적</h4>
        <p>GPT-4o Vision이 제품을 깊이 이해하고 분석하여 전문 프롬프트와 Visual DNA를 생성합니다.</p>
    </div>

    <div class="data-flow-arrow">⬇️</div>

    <div class="detail-card">
        <h3>🔹 Step 2: Creative Planning</h3>
        <h4>📌 역할 및 목적</h4>
        <p>AI 감독이 3개의 Scene으로 구성된 15초 광고 시나리오를 자동 기획합니다.</p>
    </div>

    <div class="data-flow-arrow">⬇️</div>

    <div class="detail-card">
        <h3>🔹 Step 3: Control Maps Generation</h3>
        <h4>📌 역할 및 목적</h4>
        <p>영상 생성을 위한 4가지 가이드라인(제어맵)을 생성합니다. (Replicate API)</p>
    </div>
    """, unsafe_allow_html=True)