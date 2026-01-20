import streamlit as st
import os
from utils.helpers import API_BASE_URL, call_api, translate_to_korean

def render():
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
    
    # Step 0 결과 체크
    if not st.session_state.get('step0_results'):
        st.warning("⚠️ Step 0을 먼저 실행해주세요.")
        return

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
            # Payload 구성
            payload = {
                "image_path": target_info['processed_path'], 
                "user_prompt": st.session_state['user_prompt']
            }
            
            # 타이머 표시 공간 (버튼 바로 아래)
            timer_status = st.empty()
            
            # ✅ call_api 사용 (타이머 + 타임아웃 10분 자동 적용)
            success, result, elapsed_time = call_api(
                method="POST",
                url=f"{API_BASE_URL}/api/test/step1",
                payload=payload,
                step_name="Step 1 (제품 분석)",
                status_container=timer_status
            )
            
            if success:
                st.session_state['step1_analysis'] = result['analysis']
    
    # 결과 표시
    if st.session_state.get('step1_analysis'):
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