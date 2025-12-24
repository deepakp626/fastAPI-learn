from fastapi import FastAPI
from fastapi.response import JSONResponse
from pydantic import BaseModel,Field,computed_field,field__validator
from typing import Literal,Annotated
import pickle
import pandas as pd

# import the ml model
with open('model.pkl','rb') as f:
    model = pickle.load(f)

app = FastAPI()

tier_1_cities = ['Delhi','Mumbai','Bangalore','Hyderabad','Chennai']
tier_2_cities = ['Pune','Kolkata','Ahmedabad','Surat','Visakhapatnam','Jaipur','Lucknow','Indore','Patna','Coimbatore','Visakhapatnam']

# pydantic model to validate the incoming data
class UserInput(BaseModel):
    age: Annotated[int,Field(...,gt=0,lt=120,description='age of the patient')]
    weight: Annotated[int,Field(...,gt=0,description='weight of the patient')]
    height: Annotated[int,Field(...,gt=0,description='height of the patient')]
    incoming_lpa: Annotated[int,Field(...,gt=0,description='incoming lpa of the patient')]
    city: Annotated[str,Field(...,description='city of the patient')]
    occupation: Annotated[str,Field(...,description='occupation of the patient')]

    @field__validator("city")
    @classmethod
    def normalize_city(cls,v:str) -> str:
        v = v.strip().title()
        return v

    @computed_field
    @property
    def bmi(self) -> float:
            return self.weight/(self.height**2)

    @computed_field
    @property
    def lifestyle_risk(self) -> str:
        if self.smoker and self.bmi > 30:
            return "High"
        elif self.smoker or self.bmi > 25:
            return "Medium"
        else:
            return "Low"

    @computed_field
    @property
    def age_group(self)-> str:
        if self.age < 25:
            return "young"
        elif self.age < 45:
            return "adult"
        elif self.age < 65:
            return "middle-aged"
        else:
            return "senior"

    @computed_field
    @property
    def city_tier(self)->int:
        if self.city in tier_1_cities:
            return 1
        elif self.city in tier_2_cities:
            return 2
        else:
            return 3




@app.post("/predict",response_model=)
def predict_premium(data:UserInput):
    inputDf = pd.Dataframe({
        "bmi":data.bmi,
        "age_group":data.age_group,
        "city_tier":data.city_tier
    })

    prediction = model.predict(inputDf)[0]

    return JSONResponse(status_code=200,content={"predicted_category":prediction})

