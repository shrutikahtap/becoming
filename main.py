from fastapi import HTTPException, Form, File, FastAPI, UploadFile
from typing import List, Optional, Union
from pydantic import BaseModel
from src.authentication.auth_router import authentication
from src.authentication.auth_schema import auth_credentials


app = FastAPI(title="My API", description="This is a sample API", version="1.0.0")
v= "V1"

@app.post("/credentials", tags=[v] )
async def create_credentials(
    username: str = Form(...), 
    email: str = Form(...),
    age: Optional[int] = Form(None),
    ):
      if not username or not email:
         raise HTTPException(status_code=400, detail="Username, email, and age are required fields.")
      
      return {"message": "Credentials created successfully"}

if __name__ == "__main__":
      import uvicorn
      uvicorn.run("main:app", host="localhost", port=8012, reload=True)
















'''@app.post("/test/", tags=[v])#, response_model=Item)
async def create_test(
    name: Optional[str] = Form(None), 
    email: Optional[str] = Form(None), 
    age: Optional[int] = Form(None), 
    #attachments: Optional[List[Union[UploadFile, str] | None]] = File([])
    attachments: Optional[UploadFile] = File(None)
    ):
    #item = Item(name=name, email=email, age=age, attachments=attachments)
    if not name or not email or not age:
        raise HTTPException(status_code=400, detail="Name, email, and age are required fields.")
    r = attachments.filename if attachments else None
    s = attachments.file.read() if attachments else None
    #print(f"Received item: name={name}, email={email}, age={age}, attachments={attachments, r}")

    return {"message": "Item created successfully", 
            "item": name,
            "email": email,
            "age": age,
            "attachments": r,
            "attachment_content": s
            }'''


from pydantic import BaseModel, ConfigDict
class Model(BaseModel):
  x: int
  model_config = ConfigDict(extra='allow')

m = Model(x=1, y='a')  
assert m.model_dump() == {'x': 1, 'y': 'a'}
assert m.__pydantic_extra__ == {'y': 'a'}
try:
    Model(x=1, y='a', z='b', w='c')
except Exception as e:
    assert str(e) == "Extra fields not allowed (type=value_error.extra)"