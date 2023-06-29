import openai
import streamlit as st
import locale
import time

from supabase import create_client


locale.setlocale(locale.LC_ALL, '')

@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

st.markdown(
    """
<style>
footer {
    visibility: hidden;
}
</style>
""",
    unsafe_allow_html=True,
)

supabase = init_connection()

openai.api_key = st.secrets.OPENAI_TOKEN
openai_model_version = "gpt-3.5-turbo-0613"

st.title("나에게 맞는 신발을 찾아보자!👟👞")
st.image("./data/banner.png")
st.text(f"Powerd by {openai_model_version}")


def generate_prompt(purpose, Price, Design, keywords, n=4):
    prompt = f""" 
{purpose}에 맞는 신발을 {n}개 추천해주세요. 제품의 특징을 간단하지만 장점을 극대화 해서 말해주세요.
{Price}를 넘지않은 금액이지만 오차범위 5%정도의 차이는 무시해도 됩니다.
{Design}을 고려하되, 정확하지 않아도 상관없습니다.
{keywords}가 주어질 경우, 특징에 최대한 포함되었으면 합니다.
마지막 마무리 멘트로는 가격은 실제 가격과 상이 할 수 있다는 조언이 있었으면 좋겠습니다.

예시)
목적 : 출,퇴근용
가격 : 5만원
디자인 : 모던함
키워드 : 발바닥이 편한 것

출력)
나이키 (Nike) - 탄준 스니커즈 (Tanjun Sneakers)

가격: 약 5만원
특징: 경량 소재로 발에 편안함을 제공, 깔끔한 디자인으로 다양한 스타일에 어울림
---
목적 / 용도: {purpose}
최대 가격: {Price}
디자인 : {Design}
키워드: {keywords}
---
"""
    return prompt.strip()


def request_chat_completion(prompt):
    response = openai.ChatCompletion.create(
        model=openai_model_version,
        messages=[
            {"role": "system", "content": "당신은 전문 카피라이터입니다."},
            {"role": "user", "content": prompt}
        ]
    )
    return response["choices"][0]["message"]["content"]


def write_prompt_result(prompt, result):
    data = supabase.table("prompt_results")\
        .insert({"prompt": prompt, "result": result})\
        .execute()
    print(data)


with st.form("form"):
    purpose = st.text_input("목적 / 용도")
    Price = st.number_input("최대 가격 설정", format="%d", min_value=20000, step=10000)
    Design = st.selectbox("원하는 디자인 선택", ["모던함", "심플함", "유니크함", "화려함"])
    st.text("원하는 특징!")
    col1, col2, col3 = st.columns(3)
    with col1:
        keyword_one = st.text_input(placeholder="편한 발바닥", label="keyword_1", label_visibility="collapsed")
    with col2:
        keyword_two = st.text_input(placeholder="뛰어난 내구성", label="keyword_2", label_visibility="collapsed")
    with col3:
        keyword_three = st.text_input(placeholder="베스트셀러", label="keyword_3", label_visibility="collapsed")

    submitted = st.form_submit_button("검색!")
    if submitted:
        if not purpose:
            st.error("목적을 적어주셔아합니다.")
        elif not Price:
            st.error("가격을 설정해주세요")
        elif not Design:
            st.error("디자인을 선택해주세요")
        else:
            with st.spinner('원하시는 신발을 찾는 중입니다...'):
                keywords = [keyword_one, keyword_two, keyword_three]
                keywords = [x for x in keywords if x]
                prompt = generate_prompt(purpose, Price, Design, keywords)
                response = request_chat_completion(prompt)
                write_prompt_result(prompt, response)

                result_placeholder = st.empty()

                result_text = ""
                for char in response:
                    result_text += char
                    result_placeholder.text(result_text)
                    time.sleep(0.05)

                st.success('원하는 신발 찾기 성공!')

                st.text_area(
                    label="추천 결과",
                    value=response,
                    placeholder="아직 찾지 못했습니다...",
                    height=600
                )