from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

def _strip_and_validate(value: str | None, field_label: str) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        raise ValueError(f"Название {field_label} не может быть пустым")
    return value


class Task(BaseModel):
    """Модель задачи"""
    id: UUID
    title: str
    completed: bool = False


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _strip_and_validate(value, "задачи")


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    completed: bool | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        return _strip_and_validate(value, "задачи")


class Category(BaseModel):
    """Модель категории"""
    id: UUID
    name: str


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _strip_and_validate(value, "категории")


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        return _strip_and_validate(value, "категории")


tasks: list[Task] = []
categories: list[Category] = []


def _get_task_or_404(task_id: UUID) -> Task:
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")


def _get_category_or_404(category_id: UUID) -> Category:
    for category in categories:
        if category.id == category_id:
            return category
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена")


@app.get("/tasks", response_model=list[Task], tags=["Задачи"])
def get_tasks() -> list[Task]:
    """Получить список задач"""
    return tasks


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED, tags=["Задачи"])
def create_task(payload: TaskCreate) -> Task:
    """Создать новую задачу"""
    task = Task(id=uuid4(), title=payload.title, completed=False)
    tasks.append(task)
    return task


@app.patch("/tasks/{task_id}", response_model=Task, tags=["Задачи"])
def update_task(task_id: UUID, payload: TaskUpdate) -> Task:
    """Обновить существующую задачу"""
    task = _get_task_or_404(task_id)
    if payload.title is not None:
        task.title = payload.title
    if payload.completed is not None:
        task.completed = payload.completed
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Задачи"])
def delete_task(task_id: UUID) -> None:
    """Удалить задачу"""
    task = _get_task_or_404(task_id)
    tasks.remove(task)


@app.get("/categories", response_model=list[Category], tags=["Категории"])
def get_categories() -> list[Category]:
    """Получить список категорий"""
    return categories


@app.post("/categories", response_model=Category, status_code=status.HTTP_201_CREATED, tags=["Категории"])
def create_category(payload: CategoryCreate) -> Category:
    """Создать новую категорию"""
    category = Category(id=uuid4(), name=payload.name)
    categories.append(category)
    return category


@app.patch("/categories/{category_id}", response_model=Category, tags=["Категории"])
def update_category(category_id: UUID, payload: CategoryUpdate) -> Category:
    """Обновить существующую категорию"""
    category = _get_category_or_404(category_id)
    if payload.name is not None:
        category.name = payload.name
    return category


@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Категории"])
def delete_category(category_id: UUID) -> None:
    """Удалить категорию"""
    category = _get_category_or_404(category_id)
    categories.remove(category)
