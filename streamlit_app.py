import streamlit as st
import database as db
import requests

st.title("CodEdu")

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'home_page' not in st.session_state:
    st.session_state.home_page = True
if 'learning_started' not in st.session_state:
    st.session_state.learning_started = False
if 'learning_language' not in st.session_state:
    st.session_state.learning_language = 'Python'


# --- 화면 함수 정의 ---
def show_dashboard():
    st.success(f"환영합니다, {st.session_state.user_info['username']}님!")
    st.markdown(f"**학습 수준:** {st.session_state.user_info['level']}")
    
    # 저장된 학습 언어를 세션 상태에 로드
    if 'learning_language' not in st.session_state or st.session_state.learning_language != st.session_state.user_info.get('learning_language', 'Python'):
        st.session_state.learning_language = st.session_state.user_info.get('learning_language', 'Python')

    # 현재 선택된 언어 표시
    st.markdown(f"**현재 학습 언어:** :blue[{st.session_state.learning_language}]")
    
    # 학습 통계 (현재 언어별)
    stats = db.get_user_stats(st.session_state.user_info['id'], st.session_state.learning_language)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("학습한 개념", stats['completed_chapters'])
    with col2:
        st.metric("풀어본 문제", stats['total_chapters'])
    with col3:
        st.metric("평균 점수", stats['average_score'])

    # 학습 진행 상태 (현재 언어별)
    progress = db.get_learning_progress(st.session_state.user_info['id'], st.session_state.learning_language)
    if progress:
        st.subheader(f"{st.session_state.learning_language} 학습 진행 상태")
        for p in progress:
            status = "완료" if p['completed'] else "진행중"
            st.write(f"{p['chapter']}: {status} (점수: {p['score']})")
    else:
        st.info(f"{st.session_state.learning_language} 언어로 아직 학습한 내용이 없습니다.")
    
    # 언어 변경
    st.subheader("학습 언어 변경")
    languages = ["Python", "Java", "C++", "JavaScript", "C#", "Ruby", "Go"]
    current_lang_index = languages.index(st.session_state.learning_language) if st.session_state.learning_language in languages else 0
    new_language = st.selectbox("학습 언어", languages, index=current_lang_index, key="language_select")

    
    # 수준 변경
    st.subheader("학습 수준 변경")
    new_level = st.selectbox(
        "수준",
        ["초급", "중급", "고급"],
        index=["초급", "중급", "고급"].index(st.session_state.user_info['level']),
    )
    if st.button("업데이트"):
        if db.update_user_language(st.session_state.user_info['id'], new_language):
            st.session_state.learning_language = new_language
            st.session_state.user_info['learning_language'] = new_language
            st.success("학습 언어가 업데이트되었습니다!")

        if db.update_user_level(st.session_state.user_info['id'], new_level):
            st.session_state.user_info['level'] = new_level
            st.success("수준이 업데이트되었습니다!")
        
        st.rerun()

    if st.button("학습 시작하기"):
        st.session_state.learning_started = True
        st.session_state.home_page = False
        st.rerun()

    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.session_state.learning_language = 'Python'
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
    # detailLevel은 user_info에 없을 수 있으므로 안전하게 접근
    detail_level = st.session_state.user_info.get("detailLevel", 1)
    st.write("학습 수준 : " + str(detail_level))

    # 현재 레벨에서 풀었던 문제 수 조회
    solved_count = db.get_solved_problems_count(
        st.session_state.user_info['id'], 
        detail_level,
        st.session_state.learning_language
    )
    st.write(f"현재 레벨에서 풀었던 문제 수: {solved_count}개")

    current_level = st.slider("난이도 선택", 1, 10, value=detail_level)

    if current_level == detail_level:
        problem = get_problem(current_level, 10, False)
        for i in range(len(problem)):
            problem_id, problem_title, problem_url = problem[i]
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{i+1}. [{problem_title}]({problem_url}) (ID: {problem_id})")
            with col2:
                if st.button("문제 해결", key=f"solve_{problem_id}_{i}"):
                    # 문제 해결 기록 저장
                    success = db.save_solved_problem(
                        user_id=st.session_state.user_info['id'],
                        problem_id=problem_id,
                        problem_title=problem_title,
                        problem_url=problem_url,
                        detail_level=current_level,
                        language=st.session_state.learning_language
                    )
                    if success:
                        st.success(f"'{problem_title}' 문제를 해결했습니다! ✅")
                        st.rerun()
                    else:
                        st.error("문제 해결 기록 저장에 실패했습니다.")

    

def get_problem(level : int, count : int, random : bool = False):
    result = []
    if random == True:
        random_page = random.randrange(1,11)
        url = f"https://solved.ac/api/v3/search/problem?query=level:{level}&page={random_page}"
        res = requests.get(url).json()
        selected = random.sample(problems, 10)

        return [(p["problemId"], p["titleKo"], p["url"]) for p in selected]


    url = f"https://solved.ac/api/v3/search/problem?query=level:{level}&page=1"
    res = requests.get(url).json()
    problems = res["items"][:count]
    return [(p["problemId"], p["titleKo"], f"https://www.acmicpc.net/problem/{p['problemId']}")for p in problems]


# --- 메인 라우팅 ---
if st.session_state.logged_in:
    if st.session_state.home_page == True:
        show_dashboard()
    elif st.session_state.learning_started == True:
        show_learning()

else:
    tab1, tab2 = st.tabs(["로그인", "회원가입"])
    with tab1:
        show_login()
    with tab2:
        show_register()