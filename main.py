from fastapi import FastAPI,Path,HTTPException,Query
from fastapi.responses import JSONResponse
from pydantic import Basemodel,Union,Field,computed_field,field__validator
from typing import Annotated,Literal,Optional
import json

app = FastAPI()

class Patient(Basemodel):
    id:Annotated[str,Field(...,description='ID of the patient',example=['P001'])]
    name:Annotated[str,Field(...,description='Name of the patient')]
    city:Annotated[str,Field(...,description='Name of the city')]
    age:Annotated[int,Field(...,gt=0,lt=120,description='age of the patient')]
    gender:Annotated[Literal["male","female"],Field(...,description='gender of the patient.')]
    height:Annotated[float,Field(...,gt=0,description="height of the patient mtrs")]
    weight:Annotated[float,Field(...,gt=0,description="weight of the patient in kgs")]

    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight/(self.height**2),2)
        return bmi

    @computed_field
    @property
    def verdict(self):
        if self.bmi < 18.5:
             return "Underweight"
        elif self.bmi < 25:
            return "Normal"
        elif self.bmi < 30:
            return "Normal"
        else:
            return "Obese"


def load_data():
    with open("patients.json","r")  as f:
        data = json.load(f)
    return data

def save_data(data):
    with open('patient.json','w') as f:
        json.dump(data,f)


@app.get("/")
async def hello():
    return {"message": "Hello, World!"}

@app.get("/about")
async def about():
    return {"message": "This is a sample FastAPI application."}


@app.get("/view")
def view():
    data = load_data()
    return data

@app.get("/patients/{patient_id}")
def get_patient(patient_id: str = Path(...,description="ID of the patient from DB",exmaple="P001") ):
    data = load_data()
    if patient_id in data:
        return data[patient_id]
    
    return {"message": "Patient not found"}

@app.get("/sort")
def sort_patients( sort_by: str = Query(..., description="sort on the bases of height , weight or mi"),order:str=Query("asc",description="sort order asc or desc")):
    valid_fields = ["height","weight","bmi"]
    
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by field. Must be one of {valid_fields}")

    if order not in ["asc","desc"]:
        raise HTTPException(status_code=400, detail=f"Invalid order. Must be 'asc' or 'desc'")

    data = load_data()
    sorted_data = sorted(data.values(), key=lambda x: x.get(sort_by,0), reverse=(order=="desc"))
    return sorted_data


@app.post('/create')
def create_patient(patient:Patient):
     
    #  load existing data
    data= load_data()

    #check the patient already exists
    if patient.id in data:
        raise HTTPException(status_code=400,detail="Patient already exist.")

    # new patient add to the database
    data[patient.id] = patient.model_dump(exclude=['id'])

    # save into the json file 
    save_data(data) 

    return JSONResponse(status_code=201,content={"message":"patient created successfully"})


class PatientUpdate(Basemodel):
    name:Annotated[Optional[str],Field(default=None,description='Name of the patient')]
    city:Annotated[Optional[str],Field(default=None,description='Name of the city')]
    age:Annotated[Optional[int],Field(default=None,gt=0,lt=120,description='age of the patient')]
    gender:Annotated[Optional[Literal["male","female"]],Field(default=None,description='gender of the patient.')]
    height:Annotated[Optional[float],Field(default=None,gt=0,description="height of the patient mtrs")]
    weight:Annotated[Optional[float],Field(default=None,gt=0,description="weight of the patient in kgs")]

    

@app.put("/edit/{patient_id}")
def update_patient(patient_id:str,patient_update:PatientUpdate):
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404,detail="Patient not found")

    existing_patient_info = data[patient_id]

    updated_patient_info = patient_update.model_dump(exclude_unset=True)

    for key,value in updated_patient_info.item():
            existing_patient_info[key] = value

    # existing_patient_info -> pydantic object -> update bmi + verdict 
    existing_patient_info['id'] = patient_id
    patient_pydantic_obj = Patient(**existing_patient_info)

    data[patient_id] = existing_patient_info
    
    # -> pydantic object -> dict
    existing_patient_info = patient_pydantic_obj.model_dump(exclude='id')


    # add this dict to the data
    data[patient_id] = existing_patient_info

    save_data(data)

    return JSONResponse(status_code=200,content={'message':"patient updated"})


@app.delete("/delete/{patient_id}")
def delete_patient(patient_id:str):
    data = load_data()

    if patient_id not in data:
        HTTPException(status_code=404,detail="user is not present.")

    del data[patient_id]

    return JSONResponse(status_code=200,content={"messae":"patient deleted"})


    