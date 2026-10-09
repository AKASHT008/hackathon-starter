
import os
from urllib.parse import quote_plus

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

password = os.getenv("DB_PASSWORD")
if not password:
    raise RuntimeError("Please set the DB_PASSWORD environment variable.")

DATABASE_URL = (
    f"mysql+pymysql://root:{quote_plus(password)}"
    "@127.0.0.1:3306/hackathon_db"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


app = FastAPI(title="Hackathon Starter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
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
    return {"message": "Hello from FastAPI!"}


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
        db.commit()
        return {
            "id": result.lastrowid,
            "title": title,
            "completed": False,
        }
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
