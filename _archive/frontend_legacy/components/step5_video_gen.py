import streamlit as st

def render():
    st.header("Step 5: Video Generation")
    st.warning("🚧 다음 단계 (구현 예정)")
    
    if st.session_state.get('step4_keyframes'):
        st.info("✅ Step 4 키프레임이 준비되었습니다. Step 5에서 영상을 생성할 수 있습니다.")