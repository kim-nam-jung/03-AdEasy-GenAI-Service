# frontend/app.py
import streamlit as st
from dotenv import load_dotenv

# 페이지 설정 (가장 먼저 실행)
st.set_page_config(layout="wide", page_title="ADEasy Shorts Project Debugger", page_icon="🎬")

# 환경변수 로드
load_dotenv()

# 컴포넌트 임포트
from components import (
    dashboard,
    step0_bg_removal,
    step1_analysis,
    step2_planning,
    step3_control_maps,
    step4_keyframes,
    step5_video_gen
)

# 타이틀
st.title("🎬 ADEasy Shorts Project Debugger")
st.caption("디버깅 및 테스트용 UI | Debugging & Testing Interface (Modular)")

# Session State 초기화 (데이터 흐름 유지)
if 'step0_results' not in st.session_state: st.session_state['step0_results'] = []
if 'user_prompt' not in st.session_state: st.session_state['user_prompt'] = ""
if 'step1_analysis' not in st.session_state: st.session_state['step1_analysis'] = None
if 'step2_scenario' not in st.session_state: st.session_state['step2_scenario'] = None
if 'step3_maps' not in st.session_state: st.session_state['step3_maps'] = None
if 'step4_keyframes' not in st.session_state: st.session_state['step4_keyframes'] = {}

# 탭 구성
tabs = st.tabs([
    "🏠 Main Page",
    "Step 0: Preprocessing", 
    "Step 1: Understanding", 
    "Step 2: Planning", 
    "Step 3: Control Maps", 
    "Step 4: Keyframes", 
    "Step 5: Video Gen"
])

# 각 탭에 컴포넌트 렌더링
with tabs[0]:
    dashboard.render()

with tabs[1]:
    step0_bg_removal.render()

with tabs[2]:
    step1_analysis.render()

with tabs[3]:
    step2_planning.render()

with tabs[4]:
    step3_control_maps.render()

with tabs[5]:
    step4_keyframes.render()

with tabs[6]:
    step5_video_gen.render()