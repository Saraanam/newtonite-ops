from datetime import datetime, date
from enum import Enum
from typing import Optional
import os
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, String, Integer, DateTime, Date, Text, ForeignKey, JSON, select, or_
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./newtonite.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(100))  # Demo-only credentials; use password hashing in production.
    team: Mapped[str] = mapped_column(String(50), index=True)
    role: Mapped[str] = mapped_column(String(20))

class WorkItem(Base):
    __tablename__ = "work_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(160), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    item_type: Mapped[str] = mapped_column(String(30), default="task")
    priority: Mapped[str] = mapped_column(String(20), default="medium", index=True)
    status: Mapped[str] = mapped_column(String(30), default="Open", index=True)
    team: Mapped[str] = mapped_column(String(50), index=True)
    assignee: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    created_by: Mapped[str] = mapped_column(String(50))
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Activity(Base):
    __tablename__ = "activity_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("work_items.id"), index=True)
    actor: Mapped[str] = mapped_column(String(50))
    event: Mapped[str] = mapped_column(String(50))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Idempotency(Base):
    __tablename__ = "idempotency_keys"
    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    item_id: Mapped[int] = mapped_column(Integer)

Base.metadata.create_all(engine)
app = FastAPI(title="Newtonite Operations API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginInput(BaseModel):
    username: str
    password: str

class ItemInput(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    description: str = ""
    item_type: str = "task"
    priority: str = "medium"
    team: str
    due_date: Optional[date] = None

class ItemUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=160)
    description: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    version: int

class TransitionInput(BaseModel):
    status: str

class CommentInput(BaseModel):
    comment: str = Field(min_length=1, max_length=1000)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_data():
    with SessionLocal() as db:
        if db.scalar(select(User).limit(1)):
            return
        db.add_all([
            User(username="admin", password="admin123", team="Operations", role="Admin"),
            User(username="lead", password="lead123", team="Operations", role="Lead"),
            User(username="member", password="member123", team="Operations", role="Member"),
            User(username="viewer", password="viewer123", team="Operations", role="Viewer"),
            User(username="other", password="other123", team="Finance", role="Member"),
        ])
        db.commit()

seed_data()


def current_user(authorization: Optional[str] = Header(default=None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token. Log in first.")
    username = authorization.removeprefix("Bearer ")
    user = db.scalar(select(User).where(User.username == username))
    if not user:
        raise HTTPException(401, "Invalid token")
    return user


def require_team(user: User, team: str):
    if user.team != team and user.role != "Admin":
        raise HTTPException(403, "You do not have access to this team's items")


def item_or_404(item_id: int, db: Session, user: User):
    item = db.get(WorkItem, item_id)
    if not item:
        raise HTTPException(404, "Work item not found")
    require_team(user, item.team)
    return item


def log_event(db: Session, item_id: int, actor: str, event: str, details: dict):
    db.add(Activity(item_id=item_id, actor=actor, event=event, details=details))


def item_dict(item: WorkItem):
    return {"id": item.id, "title": item.title, "description": item.description,
            "item_type": item.item_type, "priority": item.priority, "status": item.status,
            "team": item.team, "assignee": item.assignee, "created_by": item.created_by,
            "due_date": item.due_date.isoformat() if item.due_date else None,
            "version": item.version, "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat()}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/login")
def login(data: LoginInput, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == data.username))
    if not user or user.password != data.password:
        raise HTTPException(401, "Incorrect username or password")
    # For this local demo, the bearer token is the username. This is not production authentication.
    return {"token": user.username, "username": user.username, "team": user.team, "role": user.role}

@app.get("/me")
def me(user: User = Depends(current_user)):
    return {"username": user.username, "team": user.team, "role": user.role}

@app.get("/items")
def list_items(status: Optional[str] = None, priority: Optional[str] = None,
              assignee: Optional[str] = None, q: Optional[str] = None,
              page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
              db: Session = Depends(get_db), user: User = Depends(current_user)):
    stmt = select(WorkItem)
    if user.role != "Admin":
        stmt = stmt.where(WorkItem.team == user.team)
    if status: stmt = stmt.where(WorkItem.status == status)
    if priority: stmt = stmt.where(WorkItem.priority == priority)
    if assignee == "unassigned": stmt = stmt.where(WorkItem.assignee.is_(None))
    elif assignee: stmt = stmt.where(WorkItem.assignee == assignee)
    if q: stmt = stmt.where(or_(WorkItem.title.contains(q), WorkItem.description.contains(q)))
    total = len(db.scalars(stmt).all())
    items = db.scalars(stmt.order_by(WorkItem.created_at.desc()).offset((page-1)*page_size).limit(page_size)).all()
    return {"items": [item_dict(x) for x in items], "page": page, "page_size": page_size, "total": total}

@app.post("/items", status_code=201)
def create_item(data: ItemInput, idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
                db: Session = Depends(get_db), user: User = Depends(current_user)):
    require_team(user, data.team)
    if data.priority not in {"low", "medium", "high", "urgent"}:
        raise HTTPException(422, "Priority must be low, medium, high, or urgent")
    if idempotency_key:
        prior = db.get(Idempotency, idempotency_key)
        if prior:
            item = db.get(WorkItem, prior.item_id)
            return item_dict(item)
    item = WorkItem(**data.model_dump(), created_by=user.username)
    db.add(item)
    db.flush()
    log_event(db, item.id, user.username, "created", {"title": item.title})
    if idempotency_key:
        db.add(Idempotency(key=idempotency_key, item_id=item.id))
    db.commit()
    db.refresh(item)
    return item_dict(item)

@app.get("/items/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return item_dict(item_or_404(item_id, db, user))

@app.patch("/items/{item_id}")
def update_item(item_id: int, data: ItemUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = item_or_404(item_id, db, user)
    if user.role == "Viewer": raise HTTPException(403, "Viewers cannot edit items")
    if data.version != item.version:
        raise HTTPException(409, detail={"message": "This item changed. Reload and try again.", "current_version": item.version})
    changes = {}
    for field in ("title", "description", "priority", "assignee"):
        value = getattr(data, field)
        if value is not None and value != getattr(item, field):
            changes[field] = {"from": getattr(item, field), "to": value}
            setattr(item, field, value)
    item.version += 1
    item.updated_at = datetime.utcnow()
    log_event(db, item.id, user.username, "updated", changes)
    db.commit()
    db.refresh(item)
    return item_dict(item)

@app.post("/items/{item_id}/claim")
def claim_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = item_or_404(item_id, db, user)
    if user.role == "Viewer": raise HTTPException(403, "Viewers cannot claim items")
    if item.assignee is not None: raise HTTPException(409, "Item has already been claimed")
    item.assignee = user.username
    item.version += 1
    item.updated_at = datetime.utcnow()
    log_event(db, item.id, user.username, "claimed", {"assignee": user.username})
    db.commit()
    db.refresh(item)
    return item_dict(item)

TRANSITIONS = {"Open": {"In Progress"}, "In Progress": {"Awaiting Approval", "Open"},
               "Awaiting Approval": {"Resolved", "In Progress"}, "Resolved": {"Closed", "In Progress"}, "Closed": set()}

@app.post("/items/{item_id}/transition")
def transition_item(item_id: int, data: TransitionInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = item_or_404(item_id, db, user)
    if user.role == "Viewer": raise HTTPException(403, "Viewers cannot change status")
    if data.status not in TRANSITIONS.get(item.status, set()):
        raise HTTPException(400, f"Transition from {item.status} to {data.status} is not allowed")
    if item.status == "Awaiting Approval" and data.status == "Resolved" and user.role not in {"Lead", "Admin"}:
        raise HTTPException(403, "Only a team Lead or Admin can approve this item")
    old = item.status
    item.status = data.status
    item.version += 1
    item.updated_at = datetime.utcnow()
    log_event(db, item.id, user.username, "status_changed", {"from": old, "to": data.status})
    db.commit()
    db.refresh(item)
    return item_dict(item)

@app.post("/items/{item_id}/comments")
def add_comment(item_id: int, data: CommentInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = item_or_404(item_id, db, user)
    log_event(db, item.id, user.username, "comment", {"comment": data.comment})
    db.commit()
    return {"message": "Comment added"}

@app.get("/items/{item_id}/activity")
def item_activity(item_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item_or_404(item_id, db, user)
    events = db.scalars(select(Activity).where(Activity.item_id == item_id).order_by(Activity.id.desc())).all()
    return [{"id": e.id, "actor": e.actor, "event": e.event, "details": e.details, "created_at": e.created_at.isoformat()} for e in events]
