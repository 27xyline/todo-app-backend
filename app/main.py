from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from contextlib import asynccontextmanager

from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


DATABASE_URL = "postgresql+psycopg://postgres:admin@127.0.0.1:5433/postgres"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей таблиц БД"""
    id: Mapped[UUID] = mapped_column(primary_key=True, default=lambda: uuid4())


class TaskORM(Base):
    """Модель для таблицы задачи в Базе Данных"""
    __tablename__ = "tasks"

    title: Mapped[str]
    completed: Mapped[bool] = mapped_column(default=False)


class CategoryORM(Base):
    """Модель для таблицы категории в Базе Данных"""
    __tablename__ = "category"

    name: Mapped[str]


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

def get_db():
    """Функция для создания сессий с БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _strip_and_validate(value: str | None, field_label: str) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        raise ValueError(f"Название {field_label} не может быть пустым")
    if len(value) > 200:
        raise ValueError(f"Название {field_label} не может быть длиннее 200 символов")
    return value


class Task(BaseModel):
    """Модель задачи"""
    id: UUID
    title: str
    completed: bool = False


class TaskCreate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _strip_and_validate(value, "задачи")


class TaskUpdate(BaseModel):
    title: str | None = None
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
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _strip_and_validate(value, "категории")


class CategoryUpdate(BaseModel):
    name: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(ccls, value: str | None) -> str | None:
        return _strip_and_validate(value, "категории")


def task_to_model(task: TaskORM) -> Task:
    """Конвертация объекта ORM в Pydantic"""
    return Task(id=task.id, title=task.title, completed=task.completed)


@app.get("/tasks", response_model=list[Task], tags=["Задачи"])
def get_tasks(db: Session = Depends(get_db)) -> list[Task]:
    """Получить список задач"""
    tasks = db.scalars(select(TaskORM)).all()
    return [task_to_model(task) for task in tasks]


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED, tags=["Задачи"])
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> Task:
    """Создать новую задачу"""
    task = TaskORM(title=payload.title, completed=False)
    db.add(task)
    db.commit()
    return task_to_model(task)


@app.patch("/tasks/{task_id}", response_model=Task, tags=["Задачи"])
def update_task(task_id: UUID, payload: TaskUpdate, db: Session = Depends(get_db)) -> Task:
    """Обновить существующую задачу"""
    task = db.get(TaskORM, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    if payload.title:
        task.title = payload.title
    if payload.completed:
        task.completed = payload.completed
    db.commit()
    return task_to_model(task)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Задачи"])
def delete_task(task_id: UUID, db: Session = Depends(get_db)) -> None:
    """Удалить задачу"""
    task = db.get(TaskORM, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    db.delete(task)
    db.commit()


def category_to_model(category: CategoryORM) -> Category:
    """Конвертация объекта ORM в Pydantic"""
    return Category(id=category.id, name=category.name)


@app.get("/categories", response_model=list[Category], tags=["Категории"])
def get_categories(db: Session = Depends(get_db)) -> list[Category]:
    """Получить список категорий"""
    categories = db.scalars(select(CategoryORM)).all()
    return [category_to_model(category) for category in categories]


@app.post("/categories", response_model=Category, status_code=status.HTTP_201_CREATED, tags=["Категории"])
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)) -> Category:
    """Создать новую категорию"""
    category = CategoryORM(name = payload.name)
    db.add(category)
    db.commit()
    return category_to_model(category)


@app.patch("/categories/{category_id}", response_model=Category, tags=["Категории"])
def update_category(category_id: UUID, payload: CategoryUpdate, db: Session = Depends(get_db)) -> Category:
    """Обновить существующую категорию"""
    category = db.get(CategoryORM, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена")
    if payload.name:
        category.name = payload.name
    db.commit()
    return category_to_model(category)


@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Категории"])
def delete_category(category_id: UUID, db: Session = Depends(get_db)) -> None:
    """Удалить категорию"""
    category = db.get(CategoryORM, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена")
    db.delete(category)
    db.commit()
