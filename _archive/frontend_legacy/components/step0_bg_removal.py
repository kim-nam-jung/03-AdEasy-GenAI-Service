import streamlit as st
import requests
import os
from utils.helpers import API_BASE_URL, get_image_download_link, call_api

def render():
    st.header("Step 0: Input & Agentic Background Removal")
    
    st.markdown("""
    제품 이미지에서 배경을 자동으로 제거하여 제품만 남긴 투명 배경 이미지(PNG)를 생성합니다.  
    SAM 2 모델이 제품을 인식하고, GPT-4o가 결과물을 평가하여 최고 품질의 누끼 이미지를 보장합니다.
    
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
        # 타이머 전용 박스 (버튼 위에 미리 생성 - 항상 존재하지만 내용이 없으면 안 보임)
        timer_box = st.empty()
        
        if st.button("🚀 Start Pipeline (Run Step 0)", type="primary", use_container_width=True):
            if not uploaded_files:
                st.error("⚠️ **제품 이미지를 업로드해주세요!** (필수 입력)")
            elif not prompt_input or prompt_input.strip() == "":
                st.error("⚠️ **광고 요청사항을 입력해주세요!** (필수 입력)")
            else:
                st.session_state['user_prompt'] = prompt_input
                
                # 파일 및 데이터 준비
                files = [('images', (file.name, file.getvalue(), file.type)) for file in uploaded_files]
                data = {'prompt': prompt_input}
                
                # ✅ [핵심] call_api 사용 (타이머 + 타임아웃 10분 자동 적용)
                success, result, elapsed_time = call_api(
                    method="POST",
                    url=f"{API_BASE_URL}/api/test/step0",
                    files=files,
                    payload=data,
                    step_name="Step 0 (배경 제거)",
                    status_container=timer_box
                )
                
                if success:
                    st.session_state['step0_results'] = result['results']
                # 실패 시 에러 메시지는 call_api 내부에서 표시됨
    
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