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


# МОДЕЛИ ДЛЯ ЗАДАЧ
class Task(BaseModel):
    """Модель задачи"""
    id: str
    title: str
    completed: bool = False


class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str | None = None
    completed: bool | None = None


# МОДЕЛИ ДЛЯ КАТЕГОРИЙ
class Category(BaseModel):
    """Модель категории """
    id: str
    name: str


class CategoryCreate(BaseModel):
    name: str


class CategoryUpdate(BaseModel):
    name: str


# БАЗА ДАННЫХ
tasks: list[Task] = []
categories: list[Category] = []


#  CRUD ДЛЯ ЗАДАЧИ
@app.get("/tasks", response_model=list[Task], tags=["ЗАДАЧИ"])
def get_tasks():
    """Получить список задач"""
    return tasks


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED, tags=["ЗАДАЧИ"])
def create_task(payload: TaskCreate):
    """Создать новую задачу"""
    task = Task(id=str(uuid4()), title=payload.title, completed=False)
    tasks.append(task)
    return task


@app.patch("/tasks/{task_id}", response_model=Task, tags=["ЗАДАЧИ"])
def update_task(task_id: str, payload: TaskUpdate):
    """
    Обновить существующую задачу
    task_id получаем из url
    payload получаем из тела запроса
    """
    for task in tasks:
        if task.id == task_id:
            if payload.title is not None:
                task.title = payload.title
            if payload.completed is not None:
                task.completed = payload.completed
            return task

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["ЗАДАЧИ"])
def delete_task(task_id: str):
    """Удалить задачу"""
    for task in tasks:
        if task.id == task_id:
            tasks.remove(task)
            return
        
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")


#  CRUD ДЛЯ КАТЕГОРИИ
@app.get("/categories", response_model=list[Category], tags=["КАТЕГОРИИ"])
def get_categories():
    """Получить список категорий"""
    return categories


@app.post("/categories", response_model=Category, status_code=status.HTTP_201_CREATED, tags=["КАТЕГОРИИ"])
def create_category(payload: CategoryCreate):
    """Создать новую категорию"""
    category = Category(id=str(uuid4()), name=payload.name)
    categories.append(category)
    return category


@app.patch("/categories/{category_id}", response_model=Category, tags=["КАТЕГОРИИ"])
def update_category(category_id: str, payload: CategoryUpdate):
    """
    Обновить существующую категорию
    task_id получаем из url
    payload получаем из тела запроса
    """
    for category in categories:
        if category.id == category_id:
            category.name = payload.name
        return category
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")


@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["КАТЕГОРИИ"])
def delete_category(category_id: str):
    """Удалить категорию"""
    for category in categories:
        if category.id == category_id:
            categories.remove(category)
            return

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")







# class BookCreate(BaseModel):
#     book: str


# book: str = ""


# @app.get("/book")
# def get_book():
#     """Получить любимую книгу"""
#     return {"book": book, "status": "succeeded", "message": f"Любимая книга: {book}"}


# @app.post("/book", status_code=status.HTTP_201_CREATED)
# def create_book(payload: BookCreate):
#     """Сохранить любимую книгу"""
#     global book
#     book = payload.book
#     return {"book": book, "status": "succeeded"}
