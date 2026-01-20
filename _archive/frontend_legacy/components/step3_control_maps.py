import streamlit as st
import requests
import json
import os
from utils.helpers import API_BASE_URL, call_api

def render():
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
    if not st.session_state.get('step0_results'):
        st.error("⚠️ **Step 0을 먼저 실행해주세요!**")
        st.info("💡 Step 0에서 배경이 제거된 제품 이미지가 필요합니다.")
        return
    
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
                # API 호출
                payload = {"image_path": target_path}
                
                # 타이머 표시 공간 (버튼 바로 아래)
                timer_status = st.empty()
                
                # ✅ call_api 사용 (타이머 + 타임아웃 240초)
                success, result, elapsed_time = call_api(
                    method="POST",
                    url=f"{API_BASE_URL}/api/test/step3",
                    payload=payload,
                    timeout=240,  # Replicate API는 긴 시간 필요
                    step_name="Step 3 (제어맵 생성)",
                    status_container=timer_status
                )
                
                if success:
                    maps = result.get('maps', {})
                    st.session_state['step3_maps'] = maps
                    
                    # 성공 카운트
                    success_count = result.get('success_count', 0)
                    
                    if success_count == 4:
                        st.info(f"✅ **제어맵 생성 완료!** (4/4 성공)")
                    elif success_count >= 2:
                        st.warning(f"⚠️ **일부 성공** ({success_count}/4)")
                        st.info("💡 Mask와 BBox는 로컬 생성이라 항상 성공합니다. SoftEdge/Depth는 API 호출이 필요합니다.")
                    else:
                        st.error(f"❌ **생성 실패** ({success_count}/4)")
    
    # ===== 결과 표시 =====
    if st.session_state.get('step3_maps'):
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
                        
                        # ✅ 핵심 수정: step3/ 서브폴더 확인
                        # 백엔드가 step3/ 안에 저장하므로 경로 보정
                        if not os.path.exists(path):
                            # 절대 경로로 변환 시도
                            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                            path = os.path.join(base_dir, path)
                        
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
                            except Exception as e:
                                st.error(f"JSON 로드 실패: {e}")
                                st.caption(f"경로: {path}")
                        else:
                            # 이미지 표시
                            try:
                                if os.path.exists(path):
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
                                else:
                                    st.error(f"❌ 파일 없음")
                                    st.caption(f"경로: {path}")
                            except Exception as e:
                                st.error(f"이미지 로드 실패: {e}")
                                st.caption(f"경로: {path}")
                    else:
                        st.error("❌ 생성 실패")
        
        # Raw JSON (디버깅용)
        with st.expander("📄 Raw Output JSON (디버깅용)"):
            st.json(maps)
