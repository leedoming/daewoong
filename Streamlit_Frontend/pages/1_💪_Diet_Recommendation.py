import streamlit as st
import pandas as pd
from Generate_Recommendations import Generator
from random import uniform as rnd
from ImageFinder.ImageFinder import get_images_links as find_image
from streamlit_echarts import st_echarts

st.set_page_config(page_title="자동 식단 추천", page_icon="💪", layout="wide")

nutritions_values = ['열량', '지방', '포화지방', '콜레스테롤', '나트륨', '탄수화물', '섬유질', '당류', '단백질']
# Streamlit states initialization
if 'person' not in st.session_state:
    st.session_state.generated = False
    st.session_state.recommendations = None
    st.session_state.person = None
    st.session_state.weight_loss_option = None

class Person:
    def __init__(self, age, height, weight, gender, activity, meals_calories_perc, weight_loss, vegan, avoid_food, cook_tool):
        self.age = age
        self.height = height
        self.weight = weight
        self.gender = gender
        self.activity = activity
        self.meals_calories_perc = meals_calories_perc
        self.weight_loss = weight_loss
        self.vegan = vegan
        self.avoid_food = avoid_food #알레르기 연동 데이터로 수정예정
        self.cook_tool = cook_tool

    # 해리스 베네딕트 공식 활용 기초대사량 계산
    def calculate_bmr(self, ):
        if self.gender == "여성":
            bmr = 655 + (9.6 * self.weight) + (1.8 * self.height) - (4.7 * self.age)
        else:
            bmr = 66 + (13.7 * self.weight) + (5 * self.height) - (6.8 * self.age)
        return bmr

    def calculate_bmi(self, ):
        bmi = round(self.weight / ((self.height / 100) ** 2), 2)
        return bmi

    def display_result(self, ):
        bmi = self.calculate_bmi()
        bmi_string = f'{bmi} kg/m²'
        if bmi < 18.5:
            category = '저체중'
            color = 'Red'
        elif 18.5 <= bmi < 25:
            category = '정상'
            color = 'Green'
        elif 25 <= bmi < 30:
            category = '과체중'
            color = 'Yellow'
        else:
            category = '비만'
            color = 'Red'
        return bmi_string, category, color

    def calories_calculator(self):
        activites = ['거의 움직이지 않음', '조금(주 1-2회 운동)', '보통(주 3-5회 운동)', '많이(주 6-7회 운동)', '매우 많이(매일 운동)']
        weights = [1.2, 1.375, 1.55, 1.725, 1.9]
        weight = weights[activites.index(self.activity)]
        maintain_calories = self.calculate_bmr() * weight
        return maintain_calories

    def generate_recommendations(self, ):
        total_calories = self.weight_loss * self.calories_calculator()
        recommendations = []
        for meal in self.meals_calories_perc:
            meal_calories = self.meals_calories_perc[meal] * total_calories
            if meal == '아침':
                recommended_nutrition = [meal_calories, rnd(10, 30), rnd(0, 4), rnd(0, 30), rnd(0, 400), rnd(40, 75),
                                         rnd(4, 10), rnd(0, 10), rnd(30, 100)]
            elif meal == '점심':
                recommended_nutrition = [meal_calories, rnd(20, 40), rnd(0, 4), rnd(0, 30), rnd(0, 400), rnd(40, 75),
                                         rnd(4, 20), rnd(0, 10), rnd(50, 175)]
            elif meal == '저녁':
                recommended_nutrition = [meal_calories, rnd(20, 40), rnd(0, 4), rnd(0, 30), rnd(0, 400), rnd(40, 75),
                                         rnd(4, 20), rnd(0, 10), rnd(50, 175)]
            else:
                recommended_nutrition = [meal_calories, rnd(10, 30), rnd(0, 4), rnd(0, 30), rnd(0, 400), rnd(40, 75),
                                         rnd(4, 10), rnd(0, 10), rnd(30, 100)]
            generator = Generator(recommended_nutrition)
            recommended_recipes = generator.generate().json()['output']
            recommendations.append(recommended_recipes)
        for recommendation in recommendations:
            for recipe in recommendation:
                recipe['image_link'] = find_image(recipe['Name'])
        return recommendations

class Display:
    def __init__(self):
        self.plans = ["체중 유지", "조금 감소", "일반 다이어트", "집중 다이어트"]
        self.weights = [1, 0.9, 0.8, 0.6]
        self.losses = ['-0 kg/주', '-0.25 kg/주', '-0.5 kg/주', '-1 kg/주']
        pass

    def display_bmi(self, person):
        st.header('BMI 계산기')
        bmi_string, category, color = person.display_result()
        st.metric(label="Body Mass Index (BMI)", value=bmi_string)
        new_title = f'<p style="font-family:sans-serif; color:{color}; font-size: 25px;">{category}</p>'
        st.markdown(new_title, unsafe_allow_html=True)
        st.markdown(
            """
            건강 BMI 범위: 18.5 kg/m² - 25 kg/m².
            """)

    def display_bmr(self, person):
        st.header('기초대사량(BMR) 계산기')
        bmr = person.calculate_bmr()
        st.metric(label="기초대사량(BMR)", value=f'{bmr} kcal')

    def display_calories(self, person):
        st.header('칼로리 계산기')
        maintain_calories = person.calories_calculator()
        st.write(
            '기초대사량(BMR) 기반 다이어트 플랜별 일일 적정 섭취 칼로리입니다.')
        for plan, weight, loss, col in zip(self.plans, self.weights, self.losses, st.columns(4)):
            with col:
                st.metric(label=plan, value=f'{round(maintain_calories * weight)} kcal/day', delta=loss,
                          delta_color="inverse")

    def display_recommendation(self, person, recommendations):
        st.header('식단 추천')
        with st.spinner('추천 생성중...'):
            meals = person.meals_calories_perc
            st.subheader('추천 레시피:')
            for meal_name, column, recommendation in zip(meals, st.columns(len(meals)), recommendations):
                with column:
                    # st.markdown(f'<div style="text-align: center;">{meal_name.upper()}</div>', unsafe_allow_html=True)
                    st.markdown(f'##### {meal_name.upper()}')
                    for recipe in recommendation:
                        recipe_name = recipe['Name']
                        expander = st.expander(recipe_name)
                        button_label = "개인 최적화"
                        recipe_link = recipe['image_link']
                        recipe_img = f'<div><center><img src={recipe_link} alt={recipe_name}></center></div>'
                        nutritions_df = pd.DataFrame({value: [recipe[value]] for value in nutritions_values})

                        expander.markdown(recipe_img, unsafe_allow_html=True)
                        expander.markdown(
                            f'<h5 style="text-align: center;font-family:sans-serif;">영양성분 (g):</h5>',
                            unsafe_allow_html=True)
                        expander.dataframe(nutritions_df)
                        expander.markdown(f'<h5 style="text-align: center;font-family:sans-serif;">재료:</h5>',
                                          unsafe_allow_html=True)
                        print(recipe['RecipeIngredientParts'])
                        print(recipe['RecipeIngredientQuantities'])
                        for i in range(len(recipe['RecipeIngredientParts'])):
                            if len(recipe['RecipeIngredientParts']) == len(recipe['RecipeIngredientQuantities']):
                                ingredient = recipe['RecipeIngredientParts'][i]
                                #if recipe['RecipeIngredientQuantities']
                                ingredient_q = recipe['RecipeIngredientQuantities'][i]
                                expander.markdown(f"""
                                            - {ingredient} : {ingredient_q}
                                """)
                            else:
                                ingredients_q = recipe['RecipeIngredientQuantities']
                                ingredients_q.append('NA')
                                ingredient = recipe['RecipeIngredientParts'][i]
                                # if recipe['RecipeIngredientQuantities']
                                ingredient_q = ingredients_q[i]
                                expander.markdown(f"""
                                                                            - {ingredient} : {ingredient_q}
                                """)
                        expander.markdown(
                            f'<h5 style="text-align: center;font-family:sans-serif;">레시피 소개:</h5>',
                            unsafe_allow_html=True)
                        for instruction in recipe['RecipeInstructions']:
                            expander.markdown(f"""
                                        - {instruction}
                            """)
                        expander.markdown(
                            f'<h5 style="text-align: center;font-family:sans-serif;">요리 시간:</h5>',
                            unsafe_allow_html=True)
                        
                        if recipe['CookTime'] == recipe['TotalTime']:
                            expander.markdown(f"""
                                - 요리 시간: {recipe['TotalTime']}min
                            """)
                        else:
                            expander.markdown(f"""
                                    - 조리 시간: {recipe['CookTime']}min
                                    - 준비 시간: {recipe['PrepTime']}min
                                    - 총 시간: {recipe['TotalTime']}min
                                """)

                        print(recipe['Name'])

                        # 레시피별 개인 최적화
                        # if st.button(button_label):
                        # 버튼이 눌렸을 때 수행할 동작
                        # personal_category = expander.radio('최적화 기능 선택', ['대체당', '인원 수 조절', '재료 대체'])
                        # if expander.button("다음"):
                        # if personal_category == "대체당":
                        # expander.write('1. 스테비아 사용\n * 설탕 대비 약 150-300배 정도 적게 사용합니다. 차가운 음식에 사용하는 것이 좋습니다.')
                        # expander.write('2. 알룰로스 사용\n * 설탕과 같은 양으로 사용합니다. 고온에서 안정적이어서 베이킹에도 사용이 가능합니다.')
                        # elif personal_category == "용량 조절":
                        # st.number_input("")
                        # with expander.spinner("레시피 개인 최적화중..."):
                        # ori_serving = recipe['RecipeServings']
                        # recipe_scale(recipe, new_serving, ori_serving)  # 용량 조절 함수 예정 - ai 활용
                        # elif personal_category == "재료 대체":
                        # ori_ingredient = expander.selectbox(f'대체하고자 하는 재료를 선택해주세요.', ingredient in recipe['RecipeIngredientParts'])
                        # new_ingredient = expander.text_input('사용하고자 하는 재료를 입력해주세요.')
                        # if expander.button("최적화"):
                        # with expander.spinner("레시피 개인 최적화중..."):
                        # recipe_replace_ingredient(ori_ingredient, new_ingredient)  # 재료 대체 함수 예정 - ai 활용
    def recipe_scale(self, recipe, ori_serving, new_serving):
        prompt = f"Adjust the quantity of the following recipe to {new_serving} servings:\n\n{recipe}\n\nAdjusted Recipe:"

    def recipe_replace_ingredient(self, ori_ingredient, new_ingredient):
        prompt = f"If it is okay"

    def display_meal_choices(self, person, recommendations):
        st.subheader('식단을 선택해주세요:')
        # Display meal compositions choices
        if len(recommendations) == 3:
            breakfast_column, launch_column, dinner_column = st.columns(3)
            with breakfast_column:
                breakfast_choice = st.selectbox(f'아침',
                                                [recipe['Name'] for recipe in recommendations[0]])
            with launch_column:
                launch_choice = st.selectbox(f'점심',
                                             [recipe['Name'] for recipe in recommendations[1]])
            with dinner_column:
                dinner_choice = st.selectbox(f'저녁',
                                             [recipe['Name'] for recipe in recommendations[2]])
            choices = [breakfast_choice, launch_choice, dinner_choice]
        elif len(recommendations) == 4:
            breakfast_column, morning_snack, launch_column, dinner_column = st.columns(4)
            with breakfast_column:
                breakfast_choice = st.selectbox(f'아침',
                                                [recipe['Name'] for recipe in recommendations[0]])
            with morning_snack:
                morning_snack = st.selectbox(f'오전 간식',
                                             [recipe['Name'] for recipe in recommendations[1]])
            with launch_column:
                launch_choice = st.selectbox(f'점심',
                                             [recipe['Name'] for recipe in recommendations[2]])
            with dinner_column:
                dinner_choice = st.selectbox(f'저녁',
                                             [recipe['Name'] for recipe in recommendations[3]])
            choices = [breakfast_choice, morning_snack, launch_choice, dinner_choice]
        else:
            breakfast_column, morning_snack, launch_column, afternoon_snack, dinner_column = st.columns(
                5)
            with breakfast_column:
                breakfast_choice = st.selectbox(f'아침',
                                                [recipe['Name'] for recipe in recommendations[0]])
            with morning_snack:
                morning_snack = st.selectbox(f'오전 간식',
                                             [recipe['Name'] for recipe in recommendations[1]])
            with launch_column:
                launch_choice = st.selectbox(f'점심',
                                             [recipe['Name'] for recipe in recommendations[2]])
            with afternoon_snack:
                afternoon_snack = st.selectbox(f'오후 간식',
                                               [recipe['Name'] for recipe in recommendations[3]])
            with dinner_column:
                dinner_choice = st.selectbox(f'저녁',
                                             [recipe['Name'] for recipe in recommendations[4]])
            choices = [breakfast_choice, morning_snack, launch_choice, afternoon_snack,
                       dinner_choice]

            # Calculating the sum of nutritional values of the choosen recipes
        total_nutrition_values = {nutrition_value: 0 for nutrition_value in nutritions_values}
        for choice, meals_ in zip(choices, recommendations):
            for meal in meals_:
                if meal['Name'] == choice:
                    for nutrition_value in nutritions_values:
                        total_nutrition_values[nutrition_value] += meal[nutrition_value]

        total_calories_chose = total_nutrition_values['열량']
        loss_calories_chose = round(person.calories_calculator() * person.weight_loss)

        # Display corresponding graphs
        st.markdown(
            f'<h5 style="text-align: center;font-family:sans-serif;">선택한 식단 총 칼로리 vs {st.session_state.weight_loss_option} 칼로리:</h5>',
            unsafe_allow_html=True)
        total_calories_graph_options = {
            "xAxis": {
                "type": "category",
                "data": ['Total Calories you chose',
                         f"{st.session_state.weight_loss_option} Calories"],
            },
            "yAxis": {"type": "value"},
            "series": [
                {
                    "data": [
                        {"value": total_calories_chose,
                         "itemStyle": {"color": ["#33FF8D", "#FF3333"][
                             total_calories_chose > loss_calories_chose]}},
                        {"value": loss_calories_chose, "itemStyle": {"color": "#3339FF"}},
                    ],
                    "type": "bar",
                }
            ],
        }
        st_echarts(options=total_calories_graph_options, height="400px", )
        st.markdown(
            f'<h5 style="text-align: center;font-family:sans-serif;">영양 분포:</h5>',
            unsafe_allow_html=True)
        nutritions_graph_options = {
            "tooltip": {"trigger": "item"},
            "legend": {"top": "5%", "left": "center"},
            "series": [
                {
                    "name": "Nutritional Values",
                    "type": "pie",
                    "radius": ["40%", "70%"],
                    "avoidLabelOverlap": False,
                    "itemStyle": {
                        "borderRadius": 10,
                        "borderColor": "#fff",
                        "borderWidth": 2,
                    },
                    "label": {"show": False, "position": "center"},
                    "emphasis": {
                        "label": {"show": True, "fontSize": "40", "fontWeight": "bold"}
                    },
                    "labelLine": {"show": False},
                    "data": [
                        {"value": round(total_nutrition_values[total_nutrition_value]),
                         "name": total_nutrition_value}
                        for total_nutrition_value in total_nutrition_values],
                }
            ],
        }
        st_echarts(options=nutritions_graph_options, height="500px", )

display = Display()
title = "<h1 style='text-align: center;'>대웅 식단 추천 DEMO</h1>"
st.markdown(title, unsafe_allow_html=True)
# 초기 데이터 수집 폼
with st.form("recommendation_form"):
    # 건강 데이터
    st.write("건강 데이터를 입력해주세요.")
    age = st.number_input('나이', min_value=2, max_value=120, step=1)
    height = st.number_input('키(cm)', min_value=50, max_value=300, step=1)
    weight = st.number_input('체중(kg)', min_value=10, max_value=300, step=1)
    gender = st.radio('성별', ('남성', '여성'))
    activity = st.select_slider('활동량', options=['거의 움직이지 않음', '조금(주 1-2회 운동)', '보통(주 3-5회 운동)',
                                                '많이(주 6-7회 운동)',
                                                '매우 많이(매일 운동)'])
    option = st.selectbox('체중 감량 계획:', display.plans)
    st.session_state.weight_loss_option = option
    weight_loss = display.weights[display.plans.index(option)]
    number_of_meals = st.slider('일일 식사 횟수', min_value=3, max_value=5, step=1, value=3)
    if number_of_meals == 3:
        meals_calories_perc = {'breakfast': 0.35, 'lunch': 0.40, 'dinner': 0.25}
    elif number_of_meals == 4:
        meals_calories_perc = {'breakfast': 0.30, 'morning snack': 0.05, 'lunch': 0.40,
                               'dinner': 0.25}
    else:
        meals_calories_perc = {'breakfast': 0.30, 'mornings snack': 0.05, 'lunch': 0.40,
                               'afternoon snack': 0.05,
                               'dinner': 0.20}
    st.markdown("---")
    # 선호 데이터
    st.write("선호 데이터를 입력해주세요.")
    food_vegan = st.radio('식단(비건 여부)', ('일반식', '비건'))
    if food_vegan == "일반식":
        vegan = "No"
    else:
        vegan = "Yes"
    # 알레르기 식품 데이터를 연동하면 좋을듯
    avoid_food = st.text_input('피하는 식재료를 ";"로 구분해 작성해주세요',placeholder='Ingredient1;Ingredient2;...')
    st.caption('Example: Milk;eggs;butter;chicken...')
    cook_tools = ['가스레인지', '전자레인지', '에어프라이기', '오븐', '찜기']
    cook_tool = st.multiselect('사용 가능한 조리 도구를 선택하세요.', cook_tools)
    family_count = st.number_input('가구 인원(수)', min_value=1, max_value=10, step=1)

    generated = st.form_submit_button("Generate")
if generated:
    st.session_state.generated = True
    person = Person(age, height, weight, gender, activity, meals_calories_perc, weight_loss, vegan,
                    avoid_food, cook_tool)
    with st.container():
        display.display_bmi(person)
    with st.container():
        display.display_bmr(person)
    with st.container():
        display.display_calories(person)
    with st.spinner('추천 식단 생성중...'):
        recommendations = person.generate_recommendations()
        st.session_state.recommendations = recommendations
        st.session_state.person = person

if st.session_state.generated:
    with st.container():
        display.display_recommendation(st.session_state.person, st.session_state.recommendations)
        st.success('추천 식단 생성 완료!', icon="✅")
    with st.container():
        display.display_meal_choices(st.session_state.person, st.session_state.recommendations)