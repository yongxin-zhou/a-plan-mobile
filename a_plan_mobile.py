"""
A计划 - 时间管理应用（移动端单文件版本）
==========================================
将所有后端代码整合到一个文件，方便在手机 Termux 上运行。

使用方法：
1. 安装 Termux（从 F-Droid 下载）
2. 安装 Python：pkg install python
3. 安装依赖：pip install fastapi uvicorn sqlalchemy jinja2 httpx python-multipart aiofiles
4. 运行：python a_plan_mobile.py
5. 手机浏览器打开：http://127.0.0.1:8000
"""

import os
import sys
import json
import hashlib
import uuid
import threading
import asyncio
from datetime import date, timedelta, datetime
from typing import List, Optional

# ─── 环境配置 ───
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'time_manager.db')}"
JWT_SECRET = os.environ.get("JWT_SECRET", "a-plan-mobile-secret-2026")
JWT_ALGORITHM = "HS256"
HOST = "127.0.0.1"
PORT = 8000

# ─── LLM 配置（可选）───
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")

# ─── 数据库 ───
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime, ForeignKey, Float
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── 数据模型 ───

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    display_name = Column(String(50), default="")
    partner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    invite_code = Column(String(20), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    background_json = Column(Text, default="{}")


class WeeklyPlan(Base):
    __tablename__ = "weekly_plans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    year = Column(Integer, nullable=False)
    week_number = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    top3 = Column(Text, default="")
    rules = Column(Text, default="")
    anti_adhd = Column(Text, default="")
    weekly_note = Column(Text, default="")
    theme = Column(Text, default="")
    exercise_data = Column(Text, default="{}")
    balance_data = Column(Text, default="{}")


class TimeBlock(Base):
    __tablename__ = "time_blocks"
    id = Column(Integer, primary_key=True, index=True)
    week_id = Column(Integer, nullable=False)
    day_index = Column(Integer, nullable=False)
    hour = Column(Integer, nullable=False)
    slot = Column(String(10), default="up")
    content = Column(Text, default="")


class Milestone(Base):
    __tablename__ = "milestones"
    id = Column(Integer, primary_key=True, index=True)
    week_id = Column(Integer, nullable=False)
    day_index = Column(Integer, nullable=False)
    content = Column(Text, default="")


class AnnualGoal(Base):
    __tablename__ = "annual_goals"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    category = Column(String(100), default="")
    content = Column(Text, default="")
    order_index = Column(Integer, default=0)


class LifePrinciple(Base):
    __tablename__ = "life_principles"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)
    content = Column(Text, default="")
    detail = Column(Text, default="")
    order_index = Column(Integer, default=0)


class SharedEvent(Base):
    __tablename__ = "shared_events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_date = Column(Date, nullable=False, index=True)
    title = Column(String(200), default="")
    description = Column(Text, default="")
    event_type = Column(String(20), default="family")
    time_range = Column(String(50), default="")


class UserSetting(Base):
    __tablename__ = "user_settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, default="")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation = Column(String(50), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, default="")
    voice_file = Column(String(255), nullable=True)
    duration = Column(Float, nullable=True, default=0)
    created_at = Column(DateTime, default=datetime.now)


class MenstrualCycle(Base):
    __tablename__ = "menstrual_cycles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    start_date = Column(Date, nullable=False, index=True)
    period_length = Column(Integer, default=5)
    cycle_length = Column(Integer, default=28)
    notes = Column(Text, default="")


class ScheduleBlock(Base):
    __tablename__ = "schedule_blocks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    date = Column(Date, nullable=False, index=True)
    start_minutes = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    block_type = Column(String(20), default="focus_90")
    label = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.now)


class CoupleGoal(Base):
    __tablename__ = "couple_goals"
    id = Column(Integer, primary_key=True, index=True)
    conversation = Column(String(50), nullable=False, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String(50), default="family")
    title = Column(String(200), nullable=False)
    my_view = Column(Text, default="")
    partner_view = Column(Text, default="")
    aligned_text = Column(Text, default="")
    status = Column(String(20), default="proposed")
    priority = Column(Integer, default=3)
    target_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class GoalCheckin(Base):
    __tablename__ = "goal_checkins"
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("couple_goals.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, default="")
    mood = Column(String(20), default="")
    created_at = Column(DateTime, default=datetime.now)


class CoupleAgreement(Base):
    __tablename__ = "couple_agreements"
    id = Column(Integer, primary_key=True, index=True)
    conversation = Column(String(50), nullable=False, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    frequency = Column(String(50), default="once")
    day_of_week = Column(Integer, nullable=True)
    time_range = Column(String(50), default="")
    start_date = Column(Date, nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)


# ─── FastAPI 应用 ───
from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import jwt

# 创建必要的目录
os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "templates"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "audio"), exist_ok=True)

app = FastAPI(title="A计划 - 时间管理（移动端）")

# 挂载静态文件
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
app.mount("/audio", StaticFiles(directory=os.path.join(BASE_DIR, "audio")), name="audio")

# Jinja2 模板
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# 创建数据库表
Base.metadata.create_all(bind=engine)


# ─── 认证辅助函数 ───

def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    return salt + ":" + hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()


def verify_password(password: str, hashed: str) -> bool:
    salt, key = hashed.split(":")
    return key == hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()


def create_token(user_id: int) -> str:
    return jwt.encode(
        {"uid": user_id, "exp": datetime.utcnow() + timedelta(days=30)},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )


def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization")
    if not auth:
        return None
    try:
        scheme, token = auth.split()
        if scheme.lower() != "bearer":
            return None
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return db.query(User).filter(User.id == payload["uid"]).first()
    except:
        return None


# ─── 周计划辅助函数 ───

def get_week_date_range(year: int, week_number: int) -> tuple[date, date]:
    jan4 = date(year, 1, 4)
    start_of_week1 = jan4 - timedelta(days=jan4.isoweekday() - 1)
    monday = start_of_week1 + timedelta(weeks=week_number - 1)
    return monday, monday + timedelta(days=6)


def get_or_create_week(db: Session, year: int, week_number: int, user_id: int = None) -> WeeklyPlan:
    filters = [WeeklyPlan.year == year, WeeklyPlan.week_number == week_number]
    if user_id:
        filters.append(WeeklyPlan.user_id == user_id)
    else:
        filters.append(WeeklyPlan.user_id == None)

    plan = db.query(WeeklyPlan).filter(*filters).first()

    if not plan and user_id:
        unowned = db.query(WeeklyPlan).filter(
            WeeklyPlan.year == year,
            WeeklyPlan.week_number == week_number,
            WeeklyPlan.user_id == None
        ).first()
        if unowned:
            unowned.user_id = user_id
            db.commit()
            db.refresh(unowned)
            return unowned

    if not plan:
        start_date, end_date = get_week_date_range(year, week_number)
        plan = WeeklyPlan(
            year=year, week_number=week_number,
            start_date=start_date, end_date=end_date,
            user_id=user_id,
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
    return plan


# ─── Pydantic 模型 ───

class WeeklyPlanCreate(BaseModel):
    year: int
    week_number: int
    top3: str = ""
    rules: str = ""
    anti_adhd: str = ""
    weekly_note: str = ""
    theme: str = ""
    exercise_data: str = "{}"
    balance_data: str = "{}"


class TimeBlockData(BaseModel):
    day_index: int
    hour: int
    slot: str = "up"
    content: str = ""


class TimeBlockBatch(BaseModel):
    blocks: list[TimeBlockData]


class MilestoneData(BaseModel):
    day_index: int
    content: str = ""


class AnnualGoalData(BaseModel):
    category: str = ""
    content: str = ""
    order_index: int = 0


# ═══════════════════════════════════════════════
# ─── API 路由 ───
# ═══════════════════════════════════════════════

# ─── 首页 ───

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


# ─── 认证路由 ───

@app.post("/api/auth/register")
def register(data: dict, db: Session = Depends(get_db)):
    username = data.get("username", "").strip()
    password = data.get("password", "")
    display_name = data.get("display_name", username)

    if not username or len(username) < 2:
        raise HTTPException(400, "用户名至少2个字符")
    if len(password) < 4:
        raise HTTPException(400, "密码至少4个字符")

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(400, "用户名已存在")

    user = User(
        username=username,
        password_hash=hash_password(password),
        display_name=display_name,
        invite_code=hashlib.md5((username + str(datetime.now())).encode()).hexdigest()[:8],
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "token": create_token(user.id),
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "invite_code": user.invite_code,
            "partner_id": user.partner_id
        }
    }


@app.post("/api/auth/login")
def login(data: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.get("username", "")).first()
    if not user or not verify_password(data.get("password", ""), user.password_hash):
        raise HTTPException(401, "用户名或密码错误")

    return {
        "token": create_token(user.id),
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "invite_code": user.invite_code,
            "partner_id": user.partner_id
        }
    }


@app.get("/api/auth/me")
def get_me(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return {"user": None}
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "partner_id": user.partner_id,
            "invite_code": user.invite_code,
        }
    }


# ─── 伴侣路由 ───

@app.post("/api/partner/bind")
def bind_partner(data: dict, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(401, "未登录")
    if user.partner_id:
        raise HTTPException(400, "已经绑定伙伴")

    code = data.get("invite_code", "").strip()
    partner = db.query(User).filter(User.invite_code == code).first()
    if not partner:
        raise HTTPException(404, "邀请码无效")
    if partner.id == user.id:
        raise HTTPException(400, "不能绑定自己")
    if partner.partner_id:
        raise HTTPException(400, "对方已有伙伴")

    user.partner_id = partner.id
    partner.partner_id = user.id
    db.commit()

    return {"ok": True, "partner": {"id": partner.id, "display_name": partner.display_name}}


# ─── 周计划路由 ───

@app.get("/api/week/{year}/{week}")
def get_week(year: int, week: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    uid = user.id if user else None
    plan = get_or_create_week(db, year, week, uid)
    milestones = db.query(Milestone).filter(Milestone.week_id == plan.id).all()
    blocks = db.query(TimeBlock).filter(TimeBlock.week_id == plan.id).all()

    return {
        "plan": {
            "id": plan.id,
            "year": plan.year,
            "week_number": plan.week_number,
            "start_date": plan.start_date.isoformat(),
            "end_date": plan.end_date.isoformat(),
            "top3": plan.top3,
            "rules": plan.rules,
            "anti_adhd": plan.anti_adhd,
            "weekly_note": plan.weekly_note,
            "theme": plan.theme,
            "exercise_data": plan.exercise_data or "{}",
            "balance_data": plan.balance_data or "{}",
        },
        "milestones": [{"id": m.id, "day_index": m.day_index, "content": m.content} for m in milestones],
        "time_blocks": [{"id": b.id, "day_index": b.day_index, "hour": b.hour, "slot": b.slot, "content": b.content} for b in blocks],
    }


@app.put("/api/week/{year}/{week}")
def update_week(year: int, week: int, data: WeeklyPlanCreate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    uid = user.id if user else None
    plan = get_or_create_week(db, year, week, uid)
    plan.top3 = data.top3
    plan.rules = data.rules
    plan.anti_adhd = data.anti_adhd
    plan.weekly_note = data.weekly_note
    plan.theme = data.theme
    plan.exercise_data = data.exercise_data
    plan.balance_data = data.balance_data
    db.commit()
    return {"ok": True}


@app.post("/api/week/{year}/{week}/time-blocks")
def save_time_blocks(year: int, week: int, data: TimeBlockBatch, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    uid = user.id if user else None
    plan = get_or_create_week(db, year, week, uid)
    db.query(TimeBlock).filter(TimeBlock.week_id == plan.id).delete()
    for b in data.blocks:
        if b.content.strip():
            db.add(TimeBlock(week_id=plan.id, day_index=b.day_index, hour=b.hour, slot=b.slot, content=b.content))
    db.commit()
    return {"ok": True}


@app.post("/api/week/{year}/{week}/milestones")
def save_milestones(year: int, week: int, data: list[MilestoneData], request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    uid = user.id if user else None
    plan = get_or_create_week(db, year, week, uid)
    db.query(Milestone).filter(Milestone.week_id == plan.id).delete()
    for m in data:
        if m.content.strip():
            db.add(Milestone(week_id=plan.id, day_index=m.day_index, content=m.content))
    db.commit()
    return {"ok": True}


# ─── 年度目标路由 ───

@app.get("/api/annual/{year}")
def get_annual_goals(year: int, db: Session = Depends(get_db)):
    goals = db.query(AnnualGoal).filter(AnnualGoal.year == year).order_by(AnnualGoal.order_index).all()
    return [{"id": g.id, "category": g.category, "content": g.content} for g in goals]


@app.post("/api/annual/{year}")
def save_annual_goals(year: int, data: list[AnnualGoalData], db: Session = Depends(get_db)):
    db.query(AnnualGoal).filter(AnnualGoal.year == year).delete()
    for g in data:
        if g.content.strip():
            db.add(AnnualGoal(year=year, category=g.category, content=g.content, order_index=g.order_index))
    db.commit()
    return {"ok": True}


# ─── 修身原则路由 ───

@app.get("/api/principles")
def get_principles(db: Session = Depends(get_db)):
    items = db.query(LifePrinciple).order_by(LifePrinciple.order_index).all()
    return [{"id": p.id, "category": p.category, "content": p.content, "detail": p.detail} for p in items]


@app.post("/api/principles")
def save_principles(data: list[dict], db: Session = Depends(get_db)):
    db.query(LifePrinciple).delete()
    for item in data:
        if item.get("content", "").strip():
            db.add(LifePrinciple(
                category=item.get("category", ""),
                content=item.get("content", ""),
                detail=item.get("detail", ""),
                order_index=item.get("order_index", 0)
            ))
    db.commit()
    return {"ok": True}


# ─── 自知路由 ───

SELF_KNOWLEDGE_CATS = ["价值观", "人性", "advantage", "disadvantage"]


@app.get("/api/self-knowledge")
def get_self_knowledge(db: Session = Depends(get_db)):
    items = db.query(LifePrinciple).filter(
        LifePrinciple.category.in_(SELF_KNOWLEDGE_CATS)
    ).order_by(LifePrinciple.order_index).all()
    result = {cat: "" for cat in SELF_KNOWLEDGE_CATS}
    for item in items:
        result[item.category] = item.content
    return result


@app.post("/api/self-knowledge")
def save_self_knowledge(data: dict, db: Session = Depends(get_db)):
    for cat in SELF_KNOWLEDGE_CATS:
        if cat in data:
            existing = db.query(LifePrinciple).filter(
                LifePrinciple.category == cat,
                ~LifePrinciple.category.in_(["立一个志", "读一本经", "改一个过", "日行一善", "行一次孝"])
            ).first()
            if existing:
                existing.content = data[cat]
            else:
                db.add(LifePrinciple(category=cat, content=data[cat], order_index=SELF_KNOWLEDGE_CATS.index(cat)))
    db.commit()
    return {"ok": True}


# ─── 设置路由 ───

DEFAULT_SETTINGS = {
    "work_start_earliest": "07:30",
    "work_start_latest": "09:00",
    "work_hours": "8.5",
    "work_days": "1,2,3,4,5",
    "focus_minutes": "90",
    "break_minutes": "15",
    "cycle_avg_length": "28",
    "cycle_period_length": "5",
}


@app.get("/api/settings")
def get_settings(db: Session = Depends(get_db)):
    result = dict(DEFAULT_SETTINGS)
    rows = db.query(UserSetting).all()
    for r in rows:
        result[r.key] = r.value
    return result


@app.put("/api/settings")
def save_settings(data: dict, db: Session = Depends(get_db)):
    for key, value in data.items():
        existing = db.query(UserSetting).filter(UserSetting.key == key).first()
        if existing:
            existing.value = str(value)
        else:
            db.add(UserSetting(key=key, value=str(value)))
    db.commit()
    return {"ok": True}


# ─── 经期路由 ───

@app.get("/api/cycle")
def get_cycles(db: Session = Depends(get_db)):
    cycles = db.query(MenstrualCycle).order_by(MenstrualCycle.id.desc()).limit(24).all()
    return [{
        "id": c.id,
        "start_date": c.start_date.isoformat(),
        "period_length": c.period_length,
        "cycle_length": c.cycle_length,
        "notes": c.notes,
    } for c in cycles]


@app.post("/api/cycle")
def add_cycle(data: dict, db: Session = Depends(get_db)):
    cycle = MenstrualCycle(
        start_date=datetime.strptime(data["start_date"], "%Y-%m-%d").date(),
        period_length=int(data.get("period_length", 5)),
        cycle_length=int(data.get("cycle_length", 28)),
        notes=data.get("notes", ""),
    )
    db.add(cycle)
    db.commit()
    return {"ok": True, "id": cycle.id}


@app.delete("/api/cycle/{cycle_id}")
def delete_cycle(cycle_id: int, db: Session = Depends(get_db)):
    cycle = db.query(MenstrualCycle).filter(MenstrualCycle.id == cycle_id).first()
    if cycle:
        db.delete(cycle)
        db.commit()
    return {"ok": True}


# ─── 聊天路由 ───

@app.post("/api/chat/send")
def send_chat(data: dict, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(401, "未登录")

    content = (data.get("content", "") or "").strip()
    if not content:
        raise HTTPException(400, "消息不能为空")
    if not user.partner_id:
        raise HTTPException(400, "尚未绑定伴侣")

    ids = sorted([user.id, user.partner_id])
    conversation = f"{ids[0]}_{ids[1]}"
    msg = ChatMessage(conversation=conversation, sender_id=user.id, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return {"ok": True, "id": msg.id, "created_at": msg.created_at.isoformat()}


@app.get("/api/chat/messages")
def get_chat_messages(request: Request, since: int = 0, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(401, "未登录")
    if not user.partner_id:
        return []

    ids = sorted([user.id, user.partner_id])
    conversation = f"{ids[0]}_{ids[1]}"
    msgs = db.query(ChatMessage).filter(
        ChatMessage.conversation == conversation,
        ChatMessage.id > since,
    ).order_by(ChatMessage.id.asc()).all()

    return [{
        "id": m.id,
        "sender_id": m.sender_id,
        "content": m.content,
        "voice_file": m.voice_file,
        "duration": m.duration,
        "created_at": m.created_at.isoformat(),
    } for m in msgs]


# ─── 夫妻目标路由 ───

@app.get("/api/couple/goals")
def get_couple_goals(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not user.partner_id:
        return []

    ids = sorted([user.id, user.partner_id])
    conversation = f"{ids[0]}_{ids[1]}"
    goals = db.query(CoupleGoal).filter(
        CoupleGoal.conversation == conversation
    ).order_by(CoupleGoal.priority.asc(), CoupleGoal.updated_at.desc()).all()

    return [{
        "id": g.id, "creator_id": g.creator_id, "category": g.category,
        "title": g.title, "my_view": g.my_view, "partner_view": g.partner_view,
        "aligned_text": g.aligned_text, "status": g.status, "priority": g.priority,
        "target_date": g.target_date.isoformat() if g.target_date else None,
        "created_at": g.created_at.isoformat(),
    } for g in goals]


@app.post("/api/couple/goals")
def create_couple_goal(data: dict, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not user.partner_id:
        raise HTTPException(400, "尚未绑定伴侣")

    title = (data.get("title", "") or "").strip()
    if not title:
        raise HTTPException(400, "目标标题不能为空")

    ids = sorted([user.id, user.partner_id])
    conversation = f"{ids[0]}_{ids[1]}"

    goal = CoupleGoal(
        conversation=conversation,
        creator_id=user.id,
        category=data.get("category", "family"),
        title=title,
        my_view=data.get("my_view", ""),
        partner_view=data.get("partner_view", ""),
        status=data.get("status", "proposed"),
        priority=data.get("priority", 3),
        target_date=datetime.strptime(data["target_date"], "%Y-%m-%d").date() if data.get("target_date") else None,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    return {"ok": True, "id": goal.id}


@app.put("/api/couple/goals/{goal_id}")
def update_couple_goal(goal_id: int, data: dict, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(401, "未登录")

    goal = db.query(CoupleGoal).filter(CoupleGoal.id == goal_id).first()
    if not goal:
        raise HTTPException(404, "目标不存在")

    for field in ["title", "category", "aligned_text", "status", "priority", "my_view", "partner_view"]:
        if field in data:
            setattr(goal, field, data[field])

    if data.get("target_date"):
        goal.target_date = datetime.strptime(data["target_date"], "%Y-%m-%d").date()

    goal.updated_at = datetime.now()
    db.commit()

    return {"ok": True}


@app.delete("/api/couple/goals/{goal_id}")
def delete_couple_goal(goal_id: int, db: Session = Depends(get_db)):
    goal = db.query(CoupleGoal).filter(CoupleGoal.id == goal_id).first()
    if not goal:
        raise HTTPException(404, "目标不存在")
    db.query(GoalCheckin).filter(GoalCheckin.goal_id == goal_id).delete()
    db.delete(goal)
    db.commit()
    return {"ok": True}


# ─── 夫妻约定路由 ───

@app.get("/api/couple/agreements")
def get_couple_agreements(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not user.partner_id:
        return []

    ids = sorted([user.id, user.partner_id])
    conversation = f"{ids[0]}_{ids[1]}"
    items = db.query(CoupleAgreement).filter(
        CoupleAgreement.conversation == conversation,
        CoupleAgreement.is_active == 1,
    ).order_by(CoupleAgreement.created_at.desc()).all()

    return [{
        "id": a.id, "creator_id": a.creator_id, "title": a.title,
        "description": a.description, "frequency": a.frequency,
        "day_of_week": a.day_of_week, "time_range": a.time_range,
        "start_date": a.start_date.isoformat() if a.start_date else None,
        "created_at": a.created_at.isoformat(),
    } for a in items]


@app.post("/api/couple/agreements")
def create_couple_agreement(data: dict, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not user.partner_id:
        raise HTTPException(400, "尚未绑定伴侣")

    title = (data.get("title", "") or "").strip()
    if not title:
        raise HTTPException(400, "标题不能为空")

    ids = sorted([user.id, user.partner_id])
    agreement = CoupleAgreement(
        conversation=f"{ids[0]}_{ids[1]}",
        creator_id=user.id,
        title=title,
        description=data.get("description", ""),
        frequency=data.get("frequency", "once"),
        day_of_week=data.get("day_of_week"),
        time_range=data.get("time_range", ""),
        start_date=datetime.strptime(data["start_date"], "%Y-%m-%d").date() if data.get("start_date") else None,
    )
    db.add(agreement)
    db.commit()

    return {"ok": True, "id": agreement.id}


@app.put("/api/couple/agreements/{agreement_id}")
def update_couple_agreement(agreement_id: int, data: dict, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(401, "未登录")

    a = db.query(CoupleAgreement).filter(CoupleAgreement.id == agreement_id).first()
    if not a:
        raise HTTPException(404, "约定不存在")

    for field in ["title", "description", "frequency", "day_of_week", "time_range", "is_active"]:
        if field in data:
            setattr(a, field, data[field])

    if data.get("start_date"):
        a.start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()

    db.commit()
    return {"ok": True}


@app.delete("/api/couple/agreements/{agreement_id}")
def delete_couple_agreement(agreement_id: int, db: Session = Depends(get_db)):
    a = db.query(CoupleAgreement).filter(CoupleAgreement.id == agreement_id).first()
    if a:
        a.is_active = 0
        db.commit()
    return {"ok": True}


# ─── 日程路由 ───

@app.get("/api/schedule/{date_str}")
def get_schedule(date_str: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "日期格式 YYYY-MM-DD")

    uid = user.id if user else None
    blocks = db.query(ScheduleBlock).filter(
        ScheduleBlock.user_id == uid,
        ScheduleBlock.date == target_date,
    ).order_by(ScheduleBlock.start_minutes).all()

    return [{
        "id": b.id, "start_minutes": b.start_minutes,
        "duration_minutes": b.duration_minutes,
        "block_type": b.block_type, "label": b.label,
    } for b in blocks]


@app.post("/api/schedule/{date_str}")
async def save_schedule(date_str: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "日期格式 YYYY-MM-DD")

    uid = user.id if user else None
    body = await request.json()
    blocks = body if isinstance(body, list) else body.get("blocks", [])

    db.query(ScheduleBlock).filter(
        ScheduleBlock.user_id == uid,
        ScheduleBlock.date == target_date,
    ).delete()

    for item in blocks:
        dur = item.get("duration_minutes", 0)
        if dur > 0:
            db.add(ScheduleBlock(
                user_id=uid, date=target_date,
                start_minutes=item["start_minutes"],
                duration_minutes=dur,
                block_type=item.get("block_type", "focus_90"),
                label=item.get("label", ""),
            ))

    db.commit()
    return {"ok": True}


# ─── 启动 ───

if __name__ == "__main__":
    import uvicorn

    print("=" * 50)
    print("A计划 - 时间管理（移动端）")
    print("=" * 50)
    print(f"服务地址: http://{HOST}:{PORT}")
    print("按 Ctrl+C 停止服务器")
    print("=" * 50)

    uvicorn.run(app, host=HOST, port=PORT)
