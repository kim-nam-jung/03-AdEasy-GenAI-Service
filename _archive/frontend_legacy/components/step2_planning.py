import streamlit as st
import requests
import os
from utils.helpers import API_BASE_URL, translate_to_korean, call_api

def render():
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
                payload = {
                    "image_path": target_path, 
                    "analysis_data": analysis_data,
                    "user_prompt": st.session_state['user_prompt']
                }
                
                # 타이머 표시 공간 (버튼 바로 아래)
                timer_status = st.empty()
                
                # ✅ call_api 사용 (타이머 + 타임아웃 10분 자동 적용)
                success, result, elapsed_time = call_api(
                    method="POST",
                    url=f"{API_BASE_URL}/api/test/step2",
                    payload=payload,
                    step_name="Step 2 (시나리오 기획)",
                    status_container=timer_status
                )
                
                if success:
                    st.session_state['step2_scenario'] = result['scenario']

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