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


# ─── Agent 模型（手机端 AI 时间管理） ───

class StrategicGoal(Base):
    """年度战略目标"""
    __tablename__ = "strategic_goals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    year = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    category = Column(String(50), default="learning")  # learning/health/skill/philosophy
    priority = Column(Integer, default=1)  # 1-4
    progress_pct = Column(Float, default=0.0)
    status = Column(String(20), default="active")  # active/paused/completed
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class MonthlyMilestone(Base):
    """月度里程碑"""
    __tablename__ = "monthly_milestones"
    id = Column(Integer, primary_key=True, index=True)
    strategic_goal_id = Column(Integer, ForeignKey("strategic_goals.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    title = Column(String(200), default="")
    target_actions = Column(Text, default="[]")  # JSON array
    actual_actions = Column(Text, default="[]")  # JSON array
    progress_pct = Column(Float, default=0.0)
    status = Column(String(20), default="pending")  # pending/in_progress/done
    created_at = Column(DateTime, default=datetime.now)


class DailySchedule(Base):
    """LLM 生成的日计划"""
    __tablename__ = "daily_schedules"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    date = Column(Date, nullable=False, index=True)
    generated_at = Column(DateTime, nullable=True)
    start_time = Column(String(5), default="08:00")
    blocks_json = Column(Text, default="[]")
    focus_minutes = Column(Integer, default=0)
    life_minutes = Column(Integer, default=0)
    rest_minutes = Column(Integer, default=0)
    linked_goals = Column(Text, default="[]")
    user_feedback = Column(Text, default="")
    adjustment_count = Column(Integer, default=0)


class AgentConversation(Base):
    """Agent 对话记录"""
    __tablename__ = "agent_conversations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user/assistant/system
    content = Column(Text, nullable=False)
    intent = Column(String(50), default="")  # chat/plan_adjust/goal_update/voice
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


class EnhancedUserProfile(Base):
    """增强用户画像"""
    __tablename__ = "enhanced_user_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    habits_json = Column(Text, default="{}")
    preferences_json = Column(Text, default="{}")
    learning_patterns_json = Column(Text, default="{}")
    time_allocation_json = Column(Text, default='{"rest":8,"life":8,"work":8}')
    strengths_json = Column(Text, default="[]")
    growth_areas_json = Column(Text, default="[]")
    agent_notes = Column(Text, default="")
    last_analyzed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class GoalProgress(Base):
    """目标进度记录"""
    __tablename__ = "goal_progress"
    id = Column(Integer, primary_key=True, index=True)
    strategic_goal_id = Column(Integer, ForeignKey("strategic_goals.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    recorded_date = Column(Date, nullable=False, index=True)
    progress_pct = Column(Float, default=0.0)
    evidence = Column(Text, default="")
    source = Column(String(30), default="manual")  # manual/agent/daily_checkin
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

# 自动创建默认账号（如果不存在）
def _ensure_default_user():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "yongxin").first():
            u = User(
                username="yongxin",
                password_hash=hash_password("1234"),
                display_name="永鑫",
                invite_code="yongxin01",
            )
            db.add(u)
            db.commit()
            print("✅ 已创建默认账号: yongxin / 1234")
    finally:
        db.close()

# hash_password 需要先定义才能调用，所以放到后面执行
# 会在首次请求时自动检查


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


# 首次启动时创建默认账号
_ensure_default_user()


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


# ─── Agent Pydantic Schemas ───

class StrategicGoalData(BaseModel):
    title: str
    description: str = ""
    category: str = "learning"
    priority: int = 1
    progress_pct: float = 0.0
    status: str = "active"

class StrategicGoalBatch(BaseModel):
    goals: List[StrategicGoalData]

class MonthlyMilestoneData(BaseModel):
    strategic_goal_id: int
    title: str = ""
    target_actions: str = "[]"
    actual_actions: str = "[]"
    progress_pct: float = 0.0
    status: str = "pending"

class MonthlyMilestoneBatch(BaseModel):
    milestones: List[MonthlyMilestoneData]

class GoalProgressData(BaseModel):
    strategic_goal_id: int
    progress_pct: float = 0.0
    evidence: str = ""
    source: str = "manual"

class AgentChatRequest(BaseModel):
    message: str
    intent: str = "chat"  # chat/plan_adjust/goal_update

class DailyScheduleRequest(BaseModel):
    date: str  # YYYY-MM-DD
    start_time: str = "08:00"

class EnhancedProfileData(BaseModel):
    habits_json: str = "{}"
    preferences_json: str = "{}"
    learning_patterns_json: str = "{}"
    time_allocation_json: str = '{"rest":8,"life":8,"work":8}'
    strengths_json: str = "[]"
    growth_areas_json: str = "[]"
    agent_notes: str = ""


# ═══════════════════════════════════════════════
# ─── API 路由 ───
# ═══════════════════════════════════════════════

# ─── 首页 ───

@app.get("/", response_class=HTMLResponse)
@app.get("/favicon.ico", response_class=HTMLResponse)
def index(request: Request):
    try:
        return templates.TemplateResponse("index_mobile.html", {"request": request})
    except Exception:
        try:
            return templates.TemplateResponse(request, "index_mobile.html")
        except Exception as e:
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(f"Template error: {str(e)}")


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


# ═══════════════════════════════════════════════
# ─── Agent API（手机端 AI 时间管理） ───
# ═══════════════════════════════════════════════

# ─── 战略目标 CRUD ───

@app.get("/api/goals/strategic")
def get_strategic_goals(year: int = None, db: Session = Depends(get_db)):
    if year is None:
        year = datetime.now().year
    goals = db.query(StrategicGoal).filter(StrategicGoal.year == year)\
        .order_by(StrategicGoal.priority).all()
    return {"goals": [{
        "id": g.id, "title": g.title, "description": g.description,
        "category": g.category, "priority": g.priority,
        "progress_pct": g.progress_pct, "status": g.status,
    } for g in goals]}


@app.post("/api/goals/strategic")
def save_strategic_goals(batch: StrategicGoalBatch, db: Session = Depends(get_db)):
    uid = (get_current_user(Request, db) or {"id": None}).get("id") if False else None
    # 获取当前用户
    year = datetime.now().year
    # 删除旧的，插入新的
    db.query(StrategicGoal).filter(StrategicGoal.year == year).delete()
    for i, g in enumerate(batch.goals):
        db.add(StrategicGoal(
            year=year, title=g.title, description=g.description,
            category=g.category, priority=i + 1,
            progress_pct=g.progress_pct, status=g.status,
        ))
    db.commit()
    return {"ok": True}


@app.get("/api/goals/progress")
def get_goal_progress(goal_id: int = None, days: int = 90, db: Session = Depends(get_db)):
    q = db.query(GoalProgress)
    if goal_id:
        q = q.filter(GoalProgress.strategic_goal_id == goal_id)
    cutoff = date.today() - timedelta(days=days)
    records = q.filter(GoalProgress.recorded_date >= cutoff)\
        .order_by(GoalProgress.recorded_date).all()
    return {"progress": [{
        "id": r.id, "strategic_goal_id": r.strategic_goal_id,
        "recorded_date": r.recorded_date.isoformat(),
        "progress_pct": r.progress_pct, "evidence": r.evidence,
        "source": r.source,
    } for r in records]}


@app.post("/api/goals/progress")
def record_goal_progress(data: GoalProgressData, db: Session = Depends(get_db)):
    uid = None
    try:
        auth = Request.headers.get("Authorization") if hasattr(Request, 'headers') else None
    except:
        pass
    gp = GoalProgress(
        strategic_goal_id=data.strategic_goal_id,
        recorded_date=date.today(),
        progress_pct=data.progress_pct,
        evidence=data.evidence,
        source=data.source,
    )
    db.add(gp)
    # 同步更新 StrategicGoal 的 progress_pct
    sg = db.query(StrategicGoal).get(data.strategic_goal_id)
    if sg:
        sg.progress_pct = data.progress_pct
    db.commit()
    return {"ok": True}


# ─── 月度里程碑 ───

@app.get("/api/goals/monthly-milestones")
def get_monthly_milestones(year: int = None, month: int = None, db: Session = Depends(get_db)):
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    milestones = db.query(MonthlyMilestone).filter(
        MonthlyMilestone.year == year, MonthlyMilestone.month == month
    ).all()
    return {"milestones": [{
        "id": m.id, "strategic_goal_id": m.strategic_goal_id,
        "title": m.title, "target_actions": m.target_actions,
        "actual_actions": m.actual_actions,
        "progress_pct": m.progress_pct, "status": m.status,
    } for m in milestones]}


@app.post("/api/goals/monthly-milestones")
def save_monthly_milestones(batch: MonthlyMilestoneBatch, db: Session = Depends(get_db)):
    year = datetime.now().year
    month = datetime.now().month
    db.query(MonthlyMilestone).filter(
        MonthlyMilestone.year == year, MonthlyMilestone.month == month
    ).delete()
    for m in batch.milestones:
        db.add(MonthlyMilestone(
            strategic_goal_id=m.strategic_goal_id,
            year=year, month=month, title=m.title,
            target_actions=m.target_actions, actual_actions=m.actual_actions,
            progress_pct=m.progress_pct, status=m.status,
        ))
    db.commit()
    return {"ok": True}


# ─── 增强用户画像 ───

@app.get("/api/profile/enhanced")
def get_enhanced_profile(db: Session = Depends(get_db)):
    # 尝试从 JWT 获取用户
    uid = None
    try:
        import jwt as _jwt
        auth_header = None
        # 由于 FastAPI 的 Depends 机制，这里简化处理
    except:
        pass
    profile = None
    if uid:
        profile = db.query(EnhancedUserProfile).filter(EnhancedUserProfile.user_id == uid).first()
    if not profile:
        profile = db.query(EnhancedUserProfile).first()
    if not profile:
        return {"profile": None}
    return {"profile": {
        "habits_json": profile.habits_json,
        "preferences_json": profile.preferences_json,
        "learning_patterns_json": profile.learning_patterns_json,
        "time_allocation_json": profile.time_allocation_json,
        "strengths_json": profile.strengths_json,
        "growth_areas_json": profile.growth_areas_json,
        "agent_notes": profile.agent_notes,
    }}


@app.put("/api/profile/enhanced")
def update_enhanced_profile(data: EnhancedProfileData, db: Session = Depends(get_db)):
    profile = db.query(EnhancedUserProfile).first()
    if not profile:
        profile = EnhancedUserProfile(user_id=1)
        db.add(profile)
    profile.habits_json = data.habits_json
    profile.preferences_json = data.preferences_json
    profile.learning_patterns_json = data.learning_patterns_json
    profile.time_allocation_json = data.time_allocation_json
    profile.strengths_json = data.strengths_json
    profile.growth_areas_json = data.growth_areas_json
    profile.agent_notes = data.agent_notes
    db.commit()
    return {"ok": True}


# ─── 日计划（LLM 生成） ───

@app.get("/api/schedule/daily/{date_str}")
def get_daily_schedule(date_str: str, db: Session = Depends(get_db)):
    try:
        target_date = date.fromisoformat(date_str)
    except:
        raise HTTPException(400, "日期格式错误，应为 YYYY-MM-DD")
    schedule = db.query(DailySchedule).filter(
        DailySchedule.date == target_date
    ).first()
    if not schedule:
        return {"schedule": None}
    return {"schedule": {
        "id": schedule.id, "date": schedule.date.isoformat(),
        "generated_at": schedule.generated_at.isoformat() if schedule.generated_at else None,
        "start_time": schedule.start_time,
        "blocks_json": schedule.blocks_json,
        "focus_minutes": schedule.focus_minutes,
        "life_minutes": schedule.life_minutes,
        "rest_minutes": schedule.rest_minutes,
        "linked_goals": schedule.linked_goals,
        "adjustment_count": schedule.adjustment_count,
    }}


@app.post("/api/schedule/daily/{date_str}")
def save_daily_schedule(date_str: str, blocks_json: str = "[]",
                        start_time: str = "08:00", db: Session = Depends(get_db)):
    try:
        target_date = date.fromisoformat(date_str)
    except:
        raise HTTPException(400, "日期格式错误")
    schedule = db.query(DailySchedule).filter(DailySchedule.date == target_date).first()
    if not schedule:
        schedule = DailySchedule(date=target_date)
        db.add(schedule)
    schedule.blocks_json = blocks_json
    schedule.start_time = start_time
    schedule.generated_at = datetime.now()
    # 计算各类时间
    try:
        blocks = json.loads(blocks_json) if blocks_json else []
    except:
        blocks = []
    focus = sum(b.get("duration_min", 0) for b in blocks if "focus" in b.get("type", ""))
    rest = sum(b.get("duration_min", 0) for b in blocks if "rest" in b.get("type", ""))
    life = sum(b.get("duration_min", 0) for b in blocks if b.get("type") == "life")
    schedule.focus_minutes = focus
    schedule.rest_minutes = rest
    schedule.life_minutes = life
    db.commit()
    return {"ok": True}


# ─── Agent 对话 ───

@app.get("/api/agent/history")
def get_agent_history(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    msgs = db.query(AgentConversation).order_by(AgentConversation.id.desc())\
        .offset(offset).limit(limit).all()
    msgs.reverse()  # 按时间正序
    return {"messages": [{
        "id": m.id, "role": m.role, "content": m.content,
        "intent": m.intent, "created_at": m.created_at.isoformat(),
    } for m in msgs]}


@app.post("/api/agent/chat")
def agent_chat(req: AgentChatRequest, db: Session = Depends(get_db)):
    """与 Agent 对话，支持意图识别和计划调整"""
    # 保存用户消息
    user_msg = AgentConversation(
        user_id=1, role="user", content=req.message, intent=req.intent
    )
    db.add(user_msg)
    db.commit()

    # 构建上下文
    recent = db.query(AgentConversation).order_by(AgentConversation.id.desc()).limit(10).all()
    recent.reverse()

    # 获取战略目标
    goals = db.query(StrategicGoal).filter(
        StrategicGoal.year == datetime.now().year,
        StrategicGoal.status == "active"
    ).all()
    goals_text = "\n".join([f"- {g.title}（进度{g.progress_pct}%）" for g in goals]) or "暂无战略目标"

    # 获取今日计划
    today = date.today()
    schedule = db.query(DailySchedule).filter(DailySchedule.date == today).first()
    schedule_text = schedule.blocks_json if schedule else "今日暂无计划"

    # 获取用户画像
    profile = db.query(EnhancedUserProfile).first()
    profile_text = profile.agent_notes if profile else "暂无用户画像"

    # 构建 prompt
    context = "\n".join([f"{'用户' if m.role == 'user' else '助手'}: {m.content}" for m in recent])

    system_prompt = """你是A计划，永鑫的AI时间管理搭档。

【核心价值观】
- 智慧：学习古圣先贤的智慧（四书五经、经典），将其融入日常生活决策
- 高能量：保持身心活力，合理分配精力，避免内耗和焦虑
- 长期主义：关注长期价值，不被短期波动干扰，持续积累复利
- 减少焦虑：识别焦虑来源，用行动和计划化解不确定性
- 识别环境：看清时代趋势、行业变化、自身位置，顺势而为
- 知己：深入了解自己的优势、局限、情绪模式，扬长避短
- 齐家：经营好家庭关系，夫妻同心，亲子陪伴，家庭是事业的根基
- 治国平天下：发展事业，创造价值，承担责任

【角色定位】
- 理性分析师：帮永鑫看清现状，用数据和逻辑分析
- 实战参谋：给具体可执行的建议，不讲空话
- 写作外脑：帮永鑫表达想法，弥补写作短板
- 能量守卫：当永鑫焦虑或内耗时，引导他回到正轨

【工作原则】
1. 将年度战略目标分解为可执行的月/周/日计划
2. 根据每天开始工作的时间，生成当日时间安排
3. 追踪目标进度，发现偏差时主动提醒
4. 通过对话了解工作习惯，持续优化计划
5. 遇到焦虑或压力时，引导识别问题本质，给出行动方案
6. 提醒永鑫：家庭>事业>学习，齐家是根基

时间分配原则（8h/8h/8h）：
- 休息（8h）：睡眠、午休、放松（高能量的基础）
- 生活（8h）：家庭、育儿、家务、社交（齐家）
- 工作（8h）：职业工作 + 战略学习（治国平天下）

输出要求：中文，简洁，先结论后展开。涉及计划时输出JSON格式。
遇到焦虑类话题时，先共情再分析，最后给出可执行的下一步行动。"""

    user_context = f"""当前战略目标：
{goals_text}

今日计划：{schedule_text}

用户画像备注：{profile_text}

对话历史：
{context}

用户说：{req.message}"""

    # 调用 LLM
    api_key = os.environ.get("LLM_API_KEY", "")
    api_base = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com")
    model = os.environ.get("LLM_MODEL", "deepseek-chat")

    reply_text = ""
    if api_key:
        try:
            import httpx
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_context}
                ],
                "temperature": 0.7,
                "max_tokens": 1024,
            }
            with httpx.Client(timeout=30) as client:
                resp = client.post(f"{api_base}/v1/chat/completions",
                                   json=payload, headers=headers)
                data = resp.json()
                reply_text = data["choices"][0]["message"]["content"]
        except Exception as e:
            reply_text = f"LLM 调用失败：{str(e)}。请检查 LLM_API_KEY 配置。"
    else:
        reply_text = "LLM 未配置。请在设置中配置 LLM_API_KEY 后重试。"

    # 保存助手回复
    assistant_msg = AgentConversation(
        user_id=1, role="assistant", content=reply_text, intent=req.intent
    )
    db.add(assistant_msg)
    db.commit()

    return {"reply": reply_text, "intent": req.intent}


# ─── 一键生成今日计划 ───

@app.post("/api/agent/generate-daily")
def generate_daily_schedule(req: DailyScheduleRequest, db: Session = Depends(get_db)):
    """LLM 一键生成今日日程"""
    try:
        target_date = date.fromisoformat(req.date)
    except:
        raise HTTPException(400, "日期格式错误")

    # 获取战略目标
    goals = db.query(StrategicGoal).filter(
        StrategicGoal.year == target_date.year,
        StrategicGoal.status == "active"
    ).all()
    goals_text = "\n".join([f"- {g.title}（优先级{g.priority}，进度{g.progress_pct}%）" for g in goals]) or "暂无"

    # 获取月度里程碑
    milestones = db.query(MonthlyMilestone).filter(
        MonthlyMilestone.year == target_date.year,
        MonthlyMilestone.month == target_date.month,
        MonthlyMilestone.status != "done"
    ).all()
    milestones_text = "\n".join([f"- {m.title}" for m in milestones]) or "暂无"

    # 获取用户画像
    profile = db.query(EnhancedUserProfile).first()
    alloc = json.loads(profile.time_allocation_json) if profile else {"rest": 8, "life": 8, "work": 8}

    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekday_names[target_date.weekday()]

    system_prompt = """你是A计划的日程生成器。为永鑫生成精确的日程安排。

【价值观融入】
- 高能量：90分钟专注块之间必须有15分钟休息，保护精力
- 长期主义：战略学习（商学/四书五经/英语/AI）要每天坚持，哪怕30分钟
- 减少焦虑：预留30分钟缓冲，不把日程排太满
- 齐家：生活时间要包含家庭陪伴（如接送孩子、亲子时光）
- 知己：高难度任务放在精力最好的时段

输出严格JSON格式（不要包含markdown代码块标记）：
{"blocks":[{"start":"HH:MM","duration_min":90,"type":"focus_90","label":"任务名","goal_id":null}],"summary":"安排说明","energy_tip":"能量管理建议"}

type可选值：focus_90, focus_60, rest_15, rest_10, life, sleep
规则：
- 90分钟专注块之间必须有15分钟休息
- 高难度任务放在精力最好的时段
- 战略学习分散安排，避免连续超过3小时
- 预留30分钟缓冲时间
- 睡眠和生活时间按用户配置
- summary中融入正能量鼓励"""

    user_prompt = f"""为永鑫生成{target_date.isoformat()}（{weekday}）的日程。

开始工作时间：{req.start_time}
时间分配：休息{alloc.get('rest',8)}h / 生活{alloc.get('life',8)}h / 工作{alloc.get('work',8)}h

活跃战略目标：
{goals_text}

本月未完成里程碑：
{milestones_text}

请生成精确的日程JSON。"""

    blocks = []
    summary = ""

    api_key = os.environ.get("LLM_API_KEY", "")
    api_base = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com")
    model = os.environ.get("LLM_MODEL", "deepseek-chat")

    if api_key:
        try:
            import httpx
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1024,
            }
            with httpx.Client(timeout=30) as client:
                resp = client.post(f"{api_base}/v1/chat/completions",
                                   json=payload, headers=headers)
                data = resp.json()
                reply = data["choices"][0]["message"]["content"]
                # 清理可能的 markdown 代码块标记
                reply = reply.strip()
                if reply.startswith("```"):
                    reply = reply.split("\n", 1)[-1]
                if reply.endswith("```"):
                    reply = reply.rsplit("```", 1)[0]
                reply = reply.strip()
                parsed = json.loads(reply)
                blocks = parsed.get("blocks", [])
                summary = parsed.get("summary", "")
        except Exception as e:
            summary = f"生成失败：{str(e)}"
    else:
        summary = "LLM 未配置，无法自动生成计划"

    # 保存到数据库
    schedule = db.query(DailySchedule).filter(DailySchedule.date == target_date).first()
    if not schedule:
        schedule = DailySchedule(date=target_date)
        db.add(schedule)
    schedule.blocks_json = json.dumps(blocks, ensure_ascii=False)
    schedule.start_time = req.start_time
    schedule.generated_at = datetime.now()
    focus = sum(b.get("duration_min", 0) for b in blocks if "focus" in b.get("type", ""))
    rest = sum(b.get("duration_min", 0) for b in blocks if "rest" in b.get("type", ""))
    life = sum(b.get("duration_min", 0) for b in blocks if b.get("type") == "life")
    schedule.focus_minutes = focus
    schedule.rest_minutes = rest
    schedule.life_minutes = life
    schedule.linked_goals = json.dumps([g.id for g in goals])
    db.commit()

    # 保存到对话记录
    db.add(AgentConversation(
        user_id=1, role="user", content=f"生成{target_date.isoformat()}的计划",
        intent="plan_adjust"
    ))
    db.add(AgentConversation(
        user_id=1, role="assistant",
        content=f"已生成{target_date.isoformat()}的日程。\n{summary}\n\n包含{len(blocks)}个时间段。",
        intent="plan_adjust"
    ))
    db.commit()

    return {
        "ok": True,
        "blocks": blocks,
        "summary": summary,
        "date": target_date.isoformat(),
        "focus_minutes": focus,
        "rest_minutes": rest,
        "life_minutes": life,
    }


# ─── 月度目标分解 ───

@app.post("/api/agent/decompose-monthly")
def decompose_monthly(year: int = None, month: int = None, db: Session = Depends(get_db)):
    """LLM 分解月度里程碑"""
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month

    goals = db.query(StrategicGoal).filter(
        StrategicGoal.year == year, StrategicGoal.status == "active"
    ).all()
    if not goals:
        return {"ok": False, "error": "请先设置战略目标"}

    goals_text = "\n".join([f"- {g.title}（{g.description}，进度{g.progress_pct}%）" for g in goals])

    # 已过月份的进展
    past = db.query(MonthlyMilestone).filter(
        MonthlyMilestone.year == year, MonthlyMilestone.month < month
    ).all()
    past_text = "\n".join([f"- {m.title}（{m.status}）" for m in past]) or "本月之前无记录"

    system_prompt = """你是A计划的目标分解器。将年度战略目标分解为月度里程碑。

【价值观融入】
- 长期主义：里程碑要服务于长期目标，不追求短期速成
- 智慧：四书五经的学习要与生活实践结合，不是死记硬背
- 知己：每个里程碑要考虑永鑫的实际能力和时间约束
- 齐家：家庭时间是底线，不能为了学习牺牲家庭

输出严格JSON格式（不要包含markdown代码块标记）：
{"milestones":[{"strategic_goal_id":X,"title":"里程碑标题","target_actions":["行动1","行动2"],"progress_pct":0,"status":"pending"}]}

要求：
- 每个战略目标分解为2-3个本月可验证的里程碑
- 行动要具体可执行，避免"多学习"这类模糊表述
- 考虑时间约束：每月实际可用战略学习时间约60-80小时
- 商学：关注实际商业案例，学以致用
- 四书五经：每周精读一段，写心得，联系生活
- 英语：每天30分钟听说，每周完成一个单元
- AI：每两周完成一个小项目或教程"""

    user_prompt = f"""分解{year}年{month}月的里程碑。

年度战略目标：
{goals_text}

已过月份进展：
{past_text}

请输出本月里程碑JSON。"""

    milestones = []
    api_key = os.environ.get("LLM_API_KEY", "")
    api_base = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com")
    model = os.environ.get("LLM_MODEL", "deepseek-chat")

    if api_key:
        try:
            import httpx
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1024,
            }
            with httpx.Client(timeout=30) as client:
                resp = client.post(f"{api_base}/v1/chat/completions",
                                   json=payload, headers=headers)
                data = resp.json()
                reply = data["choices"][0]["message"]["content"]
                reply = reply.strip()
                if reply.startswith("```"):
                    reply = reply.split("\n", 1)[-1]
                if reply.endswith("```"):
                    reply = reply.rsplit("```", 1)[0]
                reply = reply.strip()
                parsed = json.loads(reply)
                milestones = parsed.get("milestones", [])
        except Exception as e:
            return {"ok": False, "error": str(e)}
    else:
        return {"ok": False, "error": "LLM 未配置"}

    # 保存到数据库
    db.query(MonthlyMilestone).filter(
        MonthlyMilestone.year == year, MonthlyMilestone.month == month
    ).delete()
    for m in milestones:
        db.add(MonthlyMilestone(
            strategic_goal_id=m.get("strategic_goal_id", goals[0].id),
            year=year, month=month,
            title=m.get("title", ""),
            target_actions=json.dumps(m.get("target_actions", []), ensure_ascii=False),
            progress_pct=m.get("progress_pct", 0),
            status=m.get("status", "pending"),
        ))
    db.commit()

    return {"ok": True, "milestones": milestones, "count": len(milestones)}


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
