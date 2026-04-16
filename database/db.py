from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship
from config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"
    id             = Column(BigInteger, primary_key=True)
    username       = Column(String(64),  nullable=True)
    full_name      = Column(String(128), nullable=False)
    first_seen     = Column(DateTime, default=datetime.utcnow)
    last_seen      = Column(DateTime, default=datetime.utcnow)
    games_played   = Column(Integer, default=0)
    games_won      = Column(Integer, default=0)
    total_kills    = Column(Integer, default=0)
    times_mafia    = Column(Integer, default=0)
    times_doctor   = Column(Integer, default=0)
    times_detective= Column(Integer, default=0)
    times_sheriff  = Column(Integer, default=0)
    results        = relationship("GameResultModel", back_populates="user")

    @property
    def win_rate(self) -> float:
        return round(self.games_won / self.games_played * 100, 1) if self.games_played else 0.0


class GameModel(Base):
    __tablename__ = "games"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    chat_id      = Column(BigInteger, nullable=False, index=True)
    started_at   = Column(DateTime, default=datetime.utcnow)
    ended_at     = Column(DateTime, nullable=True)
    day_count    = Column(Integer, default=0)
    player_count = Column(Integer, default=0)
    winner_team  = Column(String(16), nullable=True)
    is_completed = Column(Boolean, default=False)
    results      = relationship("GameResultModel", back_populates="game")


class GameResultModel(Base):
    __tablename__ = "game_results"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    game_id      = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    user_id      = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    role         = Column(String(16), nullable=False)
    survived     = Column(Boolean, default=False)
    won          = Column(Boolean, default=False)
    kills        = Column(Integer, default=0)
    was_voted_out= Column(Boolean, default=False)
    game         = relationship("GameModel", back_populates="results")
    user         = relationship("UserModel", back_populates="results")


class WalletModel(Base):
    __tablename__ = "wallets"
    user_id         = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    coins           = Column(Integer, default=0)
    fake_passports  = Column(Integer, default=0)
    total_earned    = Column(Integer, default=0)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_or_create_user(uid: int, username: str, full_name: str) -> UserModel:
    async with Session() as s:
        u = await s.get(UserModel, uid)
        if not u:
            u = UserModel(id=uid, username=username, full_name=full_name)
            s.add(u)
            s.add(WalletModel(user_id=uid, coins=0, fake_passports=0, total_earned=0))
        else:
            u.username = username; u.full_name = full_name
            u.last_seen = datetime.utcnow()
            if not await s.get(WalletModel, uid):
                s.add(WalletModel(user_id=uid, coins=0, fake_passports=0, total_earned=0))
        await s.commit(); await s.refresh(u)
        return u


async def save_game_result(chat_id, day_count, player_count, winner_team, player_results):
    async with Session() as s:
        game = GameModel(chat_id=chat_id, ended_at=datetime.utcnow(),
                         day_count=day_count, player_count=player_count,
                         winner_team=winner_team, is_completed=True)
        s.add(game); await s.flush()
        for pr in player_results:
            s.add(GameResultModel(game_id=game.id, **{k: pr[k] for k in
                  ["user_id","role","survived","won","kills","was_voted_out"]}))
            u = await s.get(UserModel, pr["user_id"])
            if u:
                u.games_played += 1
                if pr.get("won"): u.games_won += 1
                u.total_kills += pr.get("kills", 0)
                r = pr["role"]
                if r in ("mafia","don","godfather","lawyer"): u.times_mafia += 1
                if r == "doctor":    u.times_doctor += 1
                if r == "detective": u.times_detective += 1
                if r == "sniper":    u.times_sheriff += 1
        await s.commit()


async def get_user_stats(uid: int) -> Optional[UserModel]:
    async with Session() as s:
        return await s.get(UserModel, uid)


async def get_top_players(limit=10) -> list[UserModel]:
    async with Session() as s:
        r = await s.execute(
            select(UserModel).where(UserModel.games_played > 0)
            .order_by(UserModel.games_won.desc()).limit(limit)
        )
        return r.scalars().all()


async def get_chat_stats(chat_id: int) -> dict:
    async with Session() as s:
        total  = await s.scalar(select(func.count(GameModel.id)).where(
            GameModel.chat_id==chat_id, GameModel.is_completed==True))
        city   = await s.scalar(select(func.count(GameModel.id)).where(
            GameModel.chat_id==chat_id, GameModel.winner_team=="city"))
        mafia  = await s.scalar(select(func.count(GameModel.id)).where(
            GameModel.chat_id==chat_id, GameModel.winner_team=="mafia"))
        return {"total_games": total or 0, "city_wins": city or 0,
                "mafia_wins": mafia or 0,
                "neutral_wins": (total or 0) - (city or 0) - (mafia or 0)}


async def get_wallet(uid: int) -> WalletModel:
    async with Session() as s:
        w = await s.get(WalletModel, uid)
        if not w:
            if not await s.get(UserModel, uid):
                s.add(UserModel(id=uid, username="", full_name="Unknown"))
            w = WalletModel(user_id=uid, coins=0, fake_passports=0, total_earned=0)
            s.add(w)
            await s.commit()
            await s.refresh(w)
        return w


async def add_coins(uid: int, amount: int) -> WalletModel:
    async with Session() as s:
        w = await s.get(WalletModel, uid)
        if not w:
            if not await s.get(UserModel, uid):
                s.add(UserModel(id=uid, username="", full_name="Unknown"))
            w = WalletModel(user_id=uid, coins=0, fake_passports=0, total_earned=0)
            s.add(w)
        w.coins = max(0, (w.coins or 0) + amount)
        if amount > 0:
            w.total_earned = (w.total_earned or 0) + amount
        await s.commit()
        await s.refresh(w)
        return w


async def buy_fake_passport(uid: int) -> tuple[bool, str, WalletModel]:
    async with Session() as s:
        w = await s.get(WalletModel, uid)
        if not w:
            if not await s.get(UserModel, uid):
                s.add(UserModel(id=uid, username="", full_name="Unknown"))
            w = WalletModel(user_id=uid, coins=0, fake_passports=0, total_earned=0)
            s.add(w)

        if (w.coins or 0) < settings.FAKE_PASSPORT_PRICE:
            await s.commit()
            await s.refresh(w)
            return False, "Tangangiz yetarli emas!", w

        w.coins -= settings.FAKE_PASSPORT_PRICE
        w.fake_passports = (w.fake_passports or 0) + 1
        await s.commit()
        await s.refresh(w)
        return True, "✅ Soxta passport xarid qilindi!", w

