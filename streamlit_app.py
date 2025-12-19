import streamlit as st

st.title("CodEdu 코딩 독학의 시작")
st.header("로그인")
username = st.text_input("아이디")
password = st.text_input("비밀번호", type="password")
level = st.selectbox("수준", ["초급", "중급", "고급"])