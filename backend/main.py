
import os
import ssl

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus

DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ.get("DB_PORT", "12601")
DB_NAME = os.environ.get("DB_NAME", "defaultdb")
DB_USER = os.environ.get("DB_USER", "avnadmin")
DB_PASSWORD = os.environ["DB_PASSWORD"]

DATABASE_URL = (
    f"mysql+pymysql://{quote_plus(DB_USER)}:"
    f"{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"ssl": {"check_hostname": True}},
)

SessionLocal = sessionmaker(bind=engine)

app = FastAPI(title="Hackathon Starter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://hackathon-starter-psi.vercel.app",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TaskCreate(BaseModel):
    title: str


@app.get("/")
def home():
    return {"message": "Hackathon Starter API is running"}


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database unavailable")


@app.get("/api/tasks")
def get_tasks(db: Session = Depends(get_db)):
    try:
        rows = db.execute(
            text(
                "SELECT id, title, completed, created_at "
                "FROM tasks ORDER BY id DESC"
            )
        ).mappings().all()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "completed": bool(row["completed"]),
                "created_at": (
                    row["created_at"].isoformat()
                    if row["created_at"] else None
                ),
            }
            for row in rows
        ]
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Could not load tasks")


@app.post("/api/tasks")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    title = task.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Task title is required")

    try:
        result = db.execute(
            text("INSERT INTO tasks (title) VALUES (:title)"),
            {"title": title},
        )
        task_id = result.lastrowid
        db.commit()
        return {"id": task_id, "title": title, "completed": False}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Could not create task")


@app.patch("/api/tasks/{task_id}")
def toggle_task(task_id: int, db: Session = Depends(get_db)):
    try:
        result = db.execute(
            text(
                "UPDATE tasks SET completed = NOT completed "
                "WHERE id = :task_id"
            ),
            {"task_id": task_id},
        )
        if result.rowcount == 0:
            db.rollback()
            raise HTTPException(status_code=404, detail="Task not found")

        db.commit()
        return {"message": "Task updated"}
    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Could not update task")


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    try:
        result = db.execute(
            text("DELETE FROM tasks WHERE id = :task_id"),
            {"task_id": task_id},
        )
        if result.rowcount == 0:
            db.rollback()
            raise HTTPException(status_code=404, detail="Task not found")

        db.commit()
        return {"message": "Task deleted"}
    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Could not delete task")
