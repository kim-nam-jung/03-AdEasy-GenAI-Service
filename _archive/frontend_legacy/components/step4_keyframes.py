import streamlit as st
import requests
import os
import json
import time
from utils.helpers import API_BASE_URL, call_api

def render():
    st.header("Step 4: Keyframe Generation (SDXL + ControlNet + IP-Adapter)")
    
    st.markdown("""
    Step 2의 **Scene별 시나리오**와 Step 3의 **제어맵**을 활용하여 각 Scene의 **Start Frame**과 **End Frame**을 생성합니다. 
    **SDXL Inpaint + ControlNet (SoftEdge, Depth) + IP-Adapter**를 사용하여 **제품 일관성**을 보장하고, 
    **시각적 연속성(Visual Continuity)** 을 유지합니다.
    
    **💡 생성되는 키프레임**  
    - **Scene 1** : Start Frame + End Frame (총 2장)  
    - **Scene 2** : Start Frame + End Frame (총 2장)  
    - **Scene 3** : Start Frame + End Frame (총 2장)  
    - **전체** : 6장의 키프레임 (704×1280, PNG)
    
    **💡 기술 스택**  
    - **SDXL Base 1.0** + **VAE Fix (fp16)** : 고품질 이미지 생성  
    - **Multi-ControlNet** : SoftEdge + Depth 동시 적용  
    - **IP-Adapter** : 제품 이미지 일관성 유지 (제품 색상, 질감 보존)  
    - **완전 로컬 실행** : L4 24GB GPU에서 실행 (VRAM ~17.56GB)
    """)
    
    st.divider()

    # ===== Step 0~3 데이터 확인 =====
    if not st.session_state.get('step0_results'):
        st.error("⚠️ **Step 0을 먼저 실행해주세요!**")
        return
    
    if not st.session_state.get('step1_analysis'):
        st.error("⚠️ **Step 1을 먼저 실행해주세요!**")
        return
    
    if not st.session_state.get('step2_scenario'):
        st.error("⚠️ **Step 2를 먼저 실행해주세요!**")
        return
    
    if not st.session_state.get('step3_maps'):
        st.error("⚠️ **Step 3을 먼저 실행해주세요!**")
        return
    
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
        
        # ✅ 경로 보정 추가
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        if 'softedge_path' in control_maps and control_maps['softedge_path']:
            with cols[0]:
                st.markdown("**SoftEdge Map**")
                try:
                    path = control_maps['softedge_path']
                    if not os.path.exists(path):
                        path = os.path.join(base_dir, path)
                    st.image(path, use_container_width=True)
                except Exception as e:
                    st.error(f"이미지 로드 실패: {e}")
        
        if 'depth_path' in control_maps and control_maps['depth_path']:
            with cols[1]:
                st.markdown("**Depth Map**")
                try:
                    path = control_maps['depth_path']
                    if not os.path.exists(path):
                        path = os.path.join(base_dir, path)
                    st.image(path, use_container_width=True)
                except Exception as e:
                    st.error(f"이미지 로드 실패: {e}")
        
        if 'mask_path' in control_maps and control_maps['mask_path']:
            with cols[2]:
                st.markdown("**Product Mask**")
                try:
                    path = control_maps['mask_path']
                    if not os.path.exists(path):
                        path = os.path.join(base_dir, path)
                    st.image(path, use_container_width=True)
                except Exception as e:
                    st.error(f"이미지 로드 실패: {e}")
    
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
            st.caption("• 약 17.56GB (L4 24GB 권장)")
            
            st.markdown("**💰 비용**")
            st.caption("• 완전 무료 (로컬 실행)")
            
            st.divider()
            
            if st.button(
                "✨ Run Step 4 (Generate Keyframes)", 
                type="primary", 
                use_container_width=True
            ):
                # 페이로드 구성
                payload = {
                    "product_image": product_image,
                    "visual_dna": visual_dna,
                    "scenario": scenario,
                    "control_maps": control_maps
                }
                
                # 타이머 표시 공간 (버튼 바로 아래)
                timer_status = st.empty()
                
                # ✅ call_api 사용 (타이머 + 타임아웃 600초)
                success, result, elapsed_time = call_api(
                    method="POST",
                    url=f"{API_BASE_URL}/api/test/step4",
                    payload=payload,
                    timeout=600,  # 10분 타임아웃 (키프레임 생성은 오래 걸림)
                    step_name="Step 4 (키프레임 생성)",
                    status_container=timer_status
                )
                
                if success:
                    keyframes = result.get('keyframes', {})
                    st.session_state['step4_keyframes'] = keyframes
                    
                    success_count = len(keyframes)
                    if success_count == 6:
                        st.info(f"✅ **키프레임 생성 완료!** (6/6 성공)")
                    else:
                        st.warning(f"⚠️ **일부 성공** ({success_count}/6)")
    
    # ===== 결과 표시 =====
    if st.session_state.get('step4_keyframes'):
        st.divider()
        st.subheader("👀 생성된 키프레임 결과")
        
        keyframes = st.session_state['step4_keyframes']
        
        # ✅ 경로 보정 함수
        def get_valid_path(path):
            """경로가 없으면 프로젝트 루트 기준으로 변환"""
            if os.path.exists(path):
                return path
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            return os.path.join(base_dir, path)
        
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
                            path = get_valid_path(keyframes[start_key])
                            if os.path.exists(path):
                                st.image(path, use_container_width=True)
                                
                                # 다운로드 버튼
                                with open(path, "rb") as f:
                                    st.download_button(
                                        "📥 다운로드",
                                        data=f,
                                        file_name=f"scene{scene_id}_start.png",
                                        mime="image/png",
                                        use_container_width=True,
                                        key=f"download_{start_key}"
                                    )
                            else:
                                st.error(f"❌ 파일 없음: {path}")
                        except Exception as e:
                            st.error(f"이미지 로드 실패: {e}")
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
                            path = get_valid_path(keyframes[end_key])
                            if os.path.exists(path):
                                st.image(path, use_container_width=True)
                                
                                # 다운로드 버튼
                                with open(path, "rb") as f:
                                    st.download_button(
                                        "📥 다운로드",
                                        data=f,
                                        file_name=f"scene{scene_id}_end.png",
                                        mime="image/png",
                                        use_container_width=True,
                                        key=f"download_{end_key}"
                                    )
                            else:
                                st.error(f"❌ 파일 없음: {path}")
                        except Exception as e:
                            st.error(f"이미지 로드 실패: {e}")
            else:
                with cols[1]:
                    st.error("❌ End Frame 생성 실패")
            
            st.divider()
        
        # Raw JSON (디버깅용)
        with st.expander("📄 Raw Output JSON (디버깅용)"):
            st.json(keyframes)