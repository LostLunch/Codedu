import streamlit as st
import database as db
import requests
import random

st.title("CodEdu")
if st.button("홈으로 돌아가기"):
    st.session_state.home_page = True
    st.session_state.learning_started = False
    st.rerun()


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

tier_list = [
    "bronze5", "bronze4", "bronze3", "bronze2", "bronze1",
    "silver5", "silver4", "silver3", "silver2", "silver1",
    "gold5", "gold4", "gold3", "gold2", "gold1",
    "platinum5", "platinum4", "platinum3", "platinum2", "platinum1",
    "diamond5", "diamond4", "diamond3", "diamond2", "diamond1",
    "ruby5", "ruby4", "ruby3", "ruby2", "ruby1"
]



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
                # detailLevel을 데이터베이스에서 가져와서 user_info에 추가
                detail_level = db.get_user_detail_level(user_info['id'], user_info.get('learning_language', 'Python'))
                st.session_state.user_info['detailLevel'] = detail_level
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
    # 현재 레벨에서 풀었던 문제 수 조회
    solved_count = db.get_solved_problems_count(
        st.session_state.user_info['id'], 
        detail_level,
        st.session_state.learning_language
    )

    if solved_count == 10:
        detail_level += 1
        # user_info 딕셔너리 업데이트 (딕셔너리는 ['key'] 형식으로 접근)
        st.session_state.user_info['detailLevel'] = detail_level
        # 데이터베이스에도 저장
        db.update_user_detail_level(
            st.session_state.user_info['id'],
            detail_level,
            st.session_state.learning_language
        )
        solved_count = 0
        

    # 현재 레벨(초급/중급/고급)에서 풀었던 문제 수 조회 (레벨별)
    current_user_level = st.session_state.user_info.get("level", "초급")
    level_solved_count = db.get_level_problems_count(
        st.session_state.user_info['id'],
        current_user_level,
        st.session_state.learning_language
    )

    # 레벨별로 10개 문제를 풀면 다음 레벨로 전환 (detail_level은 초기화하지 않음)
    if level_solved_count >= 10:
        if current_user_level == "초급":
            st.session_state.user_info["level"] = "중급"
            db.update_user_level(st.session_state.user_info['id'], "중급")
            st.success("축하합니다! 중급 레벨로 승급했습니다! 🎉")
            st.rerun()
        elif current_user_level == "중급":
            st.session_state.user_info["level"] = "고급"
            db.update_user_level(st.session_state.user_info['id'], "고급")
            st.success("축하합니다! 고급 레벨로 승급했습니다! 🎉")
            st.rerun()

    st.write("학습 수준 : " + st.session_state.user_info["level"])
    st.write("문제 난이도 레벨 : " + str(detail_level))
    st.write(f"현재 난이도에서 풀었던 문제 수: {solved_count}개 / 10개")
    st.write(f"현재 레벨({current_user_level})에서 풀었던 문제 수: {level_solved_count}개 / 10개")

    current_level = st.slider("난이도 선택", 1, 10, value=detail_level)
    if current_level == detail_level:
        problem = get_problem(current_level, 10, ifRandom = False)
        write_problem(problem,current_level)
    
    elif current_level < detail_level:
        problem = get_problem(current_level, 10, ifRandom = True)
        write_problem(problem,current_level)
    
    else:
        st.warning("아직 이 난이도가 개방되지 않았습니다")

    

def level_to_tier(level: int) -> str:
    """레벨을 tier로 변환 (레벨 1-30)
    레벨 1 = 티어 1 (Bronze V) = bronze5
    레벨 2 = 티어 2 (Bronze IV) = bronze4
    ...
    레벨 5 = 티어 5 (Bronze I) = bronze1
    레벨 6 = 티어 6 (Silver V) = silver5
    ...
    """
    if 1 <= level <= 30:
        return tier_list[level - 1]  # 레벨 1 -> 인덱스 0 (bronze5), 레벨 5 -> 인덱스 4 (bronze1)
    else:
        return "bronze5"  # 기본값

def get_problem(level : int, count : int, ifRandom : bool = False):
    # 레벨을 tier로 변환
    tier = level_to_tier(level)
    
    if ifRandom == True:
        random_page = random.randrange(1, 11)
        url = f"https://solved.ac/api/v3/search/problem?query=tier:{tier}&page={random_page}&sort=solved&direction=desc"
        res = requests.get(url).json()
        # 정확한 레벨로 필터링 (tier는 범위이므로)
        problems = [p for p in res["items"] if p["level"] == level]
        
        # 필터링된 문제가 부족하면 추가 페이지에서 가져오기
        page = random_page
        while len(problems) < 10 and page <= 20:
            page += 1
            url = f"https://solved.ac/api/v3/search/problem?query=tier:{tier}&page={page}&sort=solved&direction=desc"
            res = requests.get(url).json()
            problems.extend([p for p in res["items"] if p["level"] == level])
            if len(res["items"]) == 0:
                break
        
        if len(problems) == 0:
            return []
        
        selected = random.sample(problems, min(10, len(problems)))
        return [(p["problemId"], p["titleKo"], f"https://www.acmicpc.net/problem/{p['problemId']}") for p in selected]

    # tier로 검색한 후 정확한 레벨로 필터링
    problems = []
    page = 1
    while len(problems) < count and page <= 20:
        url = f"https://solved.ac/api/v3/search/problem?query=tier:{tier}&page={page}&sort=solved&direction=desc"
        res = requests.get(url).json()
        # 해당 레벨의 문제만 필터링
        filtered = [p for p in res["items"] if p["level"] == level]
        problems.extend(filtered)
        if len(res["items"]) == 0:
            break
        page += 1
    
    return [(p["problemId"], p["titleKo"], f"https://www.acmicpc.net/problem/{p['problemId']}") for p in problems[:count]]

def write_problem(problem, current_level):
    for i in range(len(problem)):
            problem_id, problem_title, problem_url = problem[i]
            
            # 문제가 이미 해결되었는지 확인
            is_solved = db.is_problem_solved(
                user_id=st.session_state.user_info['id'],
                problem_id=problem_id,
                detail_level=current_level,
                language=st.session_state.learning_language
            )
            
            col1, col2 = st.columns([4, 1])
            with col1:
                # 해결된 문제는 회색으로 표시
                if is_solved:
                    st.markdown(f"{i+1}. <span style='color:gray; text-decoration:line-through;'>[{problem_title}]({problem_url}) (ID: {problem_id}) ✅</span>", unsafe_allow_html=True)
                else:
                    st.write(f"{i+1}. [{problem_title}]({problem_url}) (ID: {problem_id})")
            with col2:
                if st.button("문제 해결", key=f"solve_{problem_id}_{i}", disabled=is_solved):
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
                        st.rerun()
                    else:
                        st.error("문제 해결 기록 저장에 실패했습니다.")


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