import streamlit as st
import database as db

st.title("CodEdu")

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'learning_started' not in st.session_state:
    st.session_state.learning_started = False


# --- 화면 함수 정의 ---
def show_dashboard():
    st.success(f"환영합니다, {st.session_state.user_info['username']}님!")
    st.markdown(f"**학습 수준:** {st.session_state.user_info['level']}")

    # 학습 통계
    stats = db.get_user_stats(st.session_state.user_info['id'])
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("학습한 개념", stats['completed_chapters'])
    with col2:
        st.metric("풀어본 문제", stats['total_chapters'])
    with col3:
        st.metric("평균 점수", stats['average_score'])

    # 학습 진행 상태
    progress = db.get_learning_progress(st.session_state.user_info['id'])
    if progress:
        st.subheader("학습 진행 상태")
        for p in progress:
            status = "완료" if p['completed'] else "진행중"
            st.write(f"{p['chapter']}: {status} (점수: {p['score']})")
    # 언어 변경
    st.subheader("학습 언어 변경")
    st.session_state.learning_language = st.selectbox("학습 언어", ["Python", "Java", "C++", "JavaScript", "C#", "Ruby","Go"])

    # 수준 변경
    st.subheader("학습 수준 변경")
    new_level = st.selectbox(
        "수준",
        ["초급", "중급", "고급"],
        index=["초급", "중급", "고급"].index(st.session_state.user_info['level']),
    )
    if st.button("수준 업데이트"):
        if db.update_user_level(st.session_state.user_info['id'], new_level):
            st.session_state.user_info['level'] = new_level
            st.success("수준이 업데이트되었습니다!")
            st.rerun()

    if st.button("학습 시작하기"):
        st.session_state.learning_started = True
        st.rerun()

    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.rerun()


def show_login():
    st.header("로그인")
    username = st.text_input("아이디", key="login_username")
    password = st.text_input("비밀번호", type="password", key="login_password")

    if st.button("로그인"):
        if username and password:
            success, user_info = db.verify_user(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.user_info = user_info
                st.success("로그인 성공!")
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
        else:
            st.warning("아이디와 비밀번호를 입력해주세요.")


def show_register():
    st.header("회원가입")
    new_username = st.text_input("아이디", key="reg_username")
    new_password = st.text_input("비밀번호", type="password", key="reg_password")
    confirm_password = st.text_input("비밀번호 확인", type="password", key="reg_confirm")
    new_level = st.selectbox("수준", ["초급", "중급", "고급"], key="reg_level")

    if st.button("회원가입"):
        if not new_username or not new_password:
            st.warning("아이디와 비밀번호를 입력해주세요.")
        elif new_password != confirm_password:
            st.error("비밀번호가 일치하지 않습니다.")
        else:
            success, message = db.register_user(new_username, new_password, new_level)
            if success:
                st.success(message)
                st.info("로그인 탭에서 로그인해주세요.")
            else:
                st.error(message)


def show_learning():
    st.header("학습 시작하기")
    st.session_state.learning_language = st.selectbox("학습 언어", ["Python", "Java", "C++", "JavaScript", "C#", "Ruby","Go"])
    if (st.session_state.learning_language):
        st.write()
    st.rerun()

# --- 메인 라우팅 ---
if st.session_state.logged_in:
    show_dashboard()
else:
    tab1, tab2 = st.tabs(["로그인", "회원가입"])
    with tab1:
        show_login()
    with tab2:
        show_register()