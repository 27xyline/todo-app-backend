from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


class Task(BaseModel):
    """Модель задачи"""
    id: str
    title: str
    completed: bool = False


class TaskCreate(BaseModel):
    title: str


class BookCreate(BaseModel):
    book: str


tasks: list[Task] = []
book: str = ""


@app.get("/tasks", response_model=list[Task])
def get_tasks():
    """Получить список задач"""
    return tasks


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate):
    """Создать новую задачу"""
    task = Task(id=str(uuid4()), title=payload.title, completed=False)
    tasks.append(task)
    return task


@app.get("/book")
def get_book():
    """Получить любимую книгу"""
    return {"book": book, "status": "succeeded", "message": f"Любимая книга: {book}"}


@app.post("/book", status_code=status.HTTP_201_CREATED)
def create_book(payload: BookCreate):
    """Сохранить любимую книгу"""
    global book
    book = payload.book
    return {"book": book, "status": "succeeded"}
