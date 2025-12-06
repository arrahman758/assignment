'''import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from pydantic import EmailStr, Field
from enum import Enum, IntEnum

engine = create_engine("sqlite:///isdp.db")

with Session(engine) as session:
    session.execute(text("""CREATE TABLE IF NOT EXISTS Student (id INTEGER PRIMARY KEY, name TEXT, email TEXT, age INTEGER, gender TEXT, course TEXT)"""))
    session.commit()

class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
class Student(BaseModel):
    name: str
    email: EmailStr
    age: int
    gender: GenderEnum
    course: str

app = FastAPI()
database=[]

@app.get('/')
def read_root():
    return {"name":"ali","number1":1.1,"number2":1}

@app.get('/student')
def read_students():
    with Session(engine) as session:
        result = session.execute(text("""SELECT * FROM Student"""))
        response=[]
        for row in result:
            response.append(row._asdict())
        return response

@app.post('/student')
def create_student(student: Student):
    with Session(engine) as session:
        session.execute(text("""INSERT INTO Student (name, email, age, gender, course) VALUES (:name, :email, :age, :gender, :course)"""), student.dict())
        session.commit()
    return student

@app.put('/student/{student_id}')
def update_student(student_id: int, student: Student):
    with Session(engine) as session:
        session.execute(text(f"""UPDATE Student SET name=:name, email=:email, age=:age, gender=:gender, course=:course WHERE id={student_id}"""), student.dict())
        session.commit()
    return student

@app.delete('/student/{student_id}')
def delete_student(student_id: int):
    with Session(engine) as session:
        session.execute(text(f"""DELETE FROM Student WHERE id={student_id}"""))
        session.commit()
    return {"message": "Student deleted"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)'''
    
 ort uvicorn    
from fastapi import FastAPI, HTTPException, Response
from fastapi import Cookie
from typing import Annotated
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
import random

# Database Setup
Base = declarative_base()

engine = create_engine("sqlite:///isdp.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# Database Models 


class User(Base):
    __tablename__ = "users"

    id = Column(   
impInteger, primary_key=True, index=True)
    userName = Column(String, unique=True, index=True)
    password = Column(String)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    session_token = Column(String, unique=True, index=True)


class Student(Base):
    __tablename__ = "student"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    age = Column(Integer)
    gender = Column(String)
    course = Column(String)


Base.metadata.create_all(bind=engine)


# Pydantic Models


class RegisterModel(BaseModel):
    username: str
    password: str

class LoginModel(BaseModel):
    username: str
    password: str

class StudentModel(BaseModel):
    name: str
    email: EmailStr
    age: int
    gender: str
    course: str




app = FastAPI()


#  Verify Session

def verify_session(session_id: str | None):
    if session_id is None:
        raise HTTPException(status_code=401, detail="Please login first")

    db = SessionLocal()
    session = db.query(Session).filter(Session.session_token == session_id).first()

    if not session:
        raise HTTPException(status_code=401, detail="Invalid session. Login again")

    return session.user_id



# 1. Register

@app.post("/register")
def register_user(data: RegisterModel):
    db = SessionLocal()

    existing = db.query(User).filter(User.userName == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(userName=data.username, password=data.password)
    db.add(new_user)
    db.commit()

    return {"message": "User registered successfully"}



#  Login + Set Cookie

@app.post("/login")
def login_user(data: LoginModel, response: Response):
    db = SessionLocal()

    user = db.query(User).filter(User.userName == data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Generate simple session token
    token = str(random.randint(100000, 999999))

    new_session = Session(user_id=user.id, session_token=token)
    db.add(new_session)
    db.commit()

    # Set session cookie
    response.set_cookie(key="session_id", value=token)

    return {"message": "Login successful"}


# CRUD: Protected Routes


# GET ALL STUDENTS
@app.get("/students")
def get_students(session_id: Annotated[str | None, Cookie()] = None):
    verify_session(session_id)

    db = SessionLocal()
    students = db.query(Student).all()
    return students


# CREATE STUDENT
@app.post("/students")
def create_student(data: StudentModel, session_id: Annotated[str | None, Cookie()] = None):
    verify_session(session_id)

    db = SessionLocal()

    new_student = Student(
        name=data.name,
        email=data.email,
        age=data.age,
        gender=data.gender,
        course=data.course
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return new_student


# UPDATE STUDENT
@app.put("/students/{student_id}")
def update_student(student_id: int, data: StudentModel, session_id: Annotated[str | None, Cookie()] = None):
    verify_session(session_id)

    db = SessionLocal()

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.name = data.name
    student.email = data.email
    student.age = data.age
    student.gender = data.gender
    student.course = data.course

    db.commit()

    return {"message": "Student updated successfully"}


# DELETE STUDENT
@app.delete("/students/{student_id}")
def delete_student(student_id: int, session_id: Annotated[str | None, Cookie()] = None):
    verify_session(session_id)

    db = SessionLocal()

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(student)
    db.commit()

    return {"message": "Student deleted successfully"}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
