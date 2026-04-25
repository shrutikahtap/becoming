from pydantic import BaseModel, EmailStr, constr, conint

class auth_credentials(BaseModel):
    name: constr(min_length=3, max_length=50)
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    age: conint(ge=18, le=120)