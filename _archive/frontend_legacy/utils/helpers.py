# frontend/utils/helpers.py
import streamlit as st
import requests
import base64
import os
import time

# 공통 상수
API_BASE_URL = "http://localhost:5000"

def call_api(method, url, payload=None, files=None, timeout=600, step_name="", status_container=None):
    """
    API 호출을 수행하고 시간 측정 및 결과를 반환하는 통합 헬퍼 함수
    - timeout: 기본 600초 (10분) 설정 (모든 Step 적용)
    - files: 파일 업로드 지원 (Step 0용)
    - step_name: 실행 중인 Step 이름 (예: "Step 0 (배경 제거)")
    - status_container: st.empty() 객체 (외부에서 생성하여 전달)
    - return: (success: bool, response_data: dict, elapsed_time: float)
    """
    from datetime import datetime
    
    start_time = time.time()
    start_time_str = datetime.now().strftime("%H:%M:%S")
    
    step_label = step_name if step_name else "작업"
    
    # status_container가 제공되면 사용, 아니면 내부에서 생성
    if status_container is None:
        status_container = st.empty()
    
    status_container.info(f"⏱️ {step_label} 실행 중... (시작: {start_time_str})")
    
    try:
        # API 호출 (동기 방식)
        if method.upper() == "POST":
            if files:
                # 파일 업로드 시 (Step 0) -> json 대신 data 사용
                response = requests.post(url, files=files, data=payload, timeout=timeout)
            else:
                # 일반 JSON 전송 (Step 1~5)
                response = requests.post(url, json=payload, timeout=timeout)
        else:
            # GET 요청
            response = requests.get(url, params=payload, timeout=timeout)
            
        elapsed_time = time.time() - start_time
        
        # 시간 포맷 (60초 이상이면 분 단위로 표시)
        if elapsed_time >= 60:
            minutes = int(elapsed_time // 60)
            seconds = elapsed_time % 60
            time_str = f"{minutes}분 {seconds:.1f}초"
        else:
            time_str = f"{elapsed_time:.2f}초"
        
        # 결과 처리
        if response.status_code == 200:
            status_container.success(f"✅ {step_label} 완료! **소요 시간: {time_str}**")
            return True, response.json(), elapsed_time
        else:
            status_container.error(f"❌ {step_label} 실패 (소요 시간: {time_str})")
            try:
                return False, response.json(), elapsed_time
            except:
                return False, response.text, elapsed_time
                
    except requests.exceptions.Timeout:
        elapsed_time = time.time() - start_time
        status_container.error(f"❌ {step_label} 타임아웃 ({timeout}초 초과)")
        return False, {"error": "Timeout"}, elapsed_time
    except Exception as e:
        elapsed_time = time.time() - start_time
        status_container.error(f"❌ {step_label} 연결 오류: {str(e)}")
        return False, {"error": str(e)}, elapsed_time

def translate_to_korean(text):
    """영어 텍스트를 한글로 번역 (디버깅용)"""
    try:
        # 번역은 짧으므로 timeout 10초 유지
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

def get_image_download_link(image_path, filename="image.png"):
    """이미지 다운로드 버튼 HTML 생성 (필요 시 사용)"""
    try:
        if not os.path.exists(image_path):
            return None
            
        with open(image_path, "rb") as file:
            img_bytes = file.read()
        
        # Base64 인코딩
        b64 = base64.b64encode(img_bytes).decode()
        
        # 다운로드 버튼 생성
        href = f'<a href="data:image/png;base64,{b64}" download="{filename}">📥 다운로드</a>'
        return href
    except Exception as e:
        return f"⚠️ 다운로드 실패: {str(e)}"