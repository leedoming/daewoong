from fastapi import FastAPI
from pydantic import BaseModel,conlist
from typing import List,Optional
import pandas as pd
from model import recommend,output_recommended_recipes
import gzip

#with gzip.open("../Data/dataset.csv", 'rt', encoding='utf-8') as file:
dataset = pd.read_csv("../Data/recipes_new.csv")
#데이터 영양소 컬럼명 영문에서 한글 변환
new_columns = {'Calories':'열량','FatContent':'지방','SaturatedFatContent':'포화지방','CholesterolContent':'콜레스테롤','SodiumContent':'나트륨','CarbohydrateContent':'탄수화물','FiberContent':'섬유질','SugarContent':'당류','ProteinContent':'단백질'}
dataset.rename(columns=new_columns, inplace=True)
print(dataset.head())
print(dataset.columns)
app = FastAPI()

class params(BaseModel):
    n_neighbors:int=5
    return_distance:bool=False

class PredictionIn(BaseModel):
    nutrition_input:conlist(float, min_items=9, max_items=9)
    ingredients:list[str]=[]
    params:Optional[params]

class Recipe(BaseModel):
    RecipeCategory:str
    Name:str
    CookTime:str
    PrepTime:str
    TotalTime:str
    RecipeIngredientParts: list[str]
    RecipeIngredientQuantities: list[str]
    RecipeServings: str
    열량:float
    지방:float
    포화지방:float
    콜레스테롤:float
    나트륨:float
    탄수화물:float
    섬유질:float
    당류:float
    단백질:float
    RecipeInstructions: List[str]
    Vegan:str
    Dessert:str

class PredictionOut(BaseModel):
    output: Optional[List[Recipe]] = None

@app.get("/")
def home():
    return {"health_check": "OK"}
@app.post("/predict/",response_model=PredictionOut)
def update_item(prediction_input:PredictionIn):
    recommendation_dataframe=recommend(dataset,prediction_input.nutrition_input,prediction_input.ingredients,prediction_input.params.dict())
    output=output_recommended_recipes(recommendation_dataframe)
    if output is None:
        return {"output":None}
    else:
        return {"output":output}

