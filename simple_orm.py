import os.path
import time
from dataclasses import dataclass
from types import ModuleType

from .exceptions import DoesNotExist
from typing import Optional, TypeVar, Type, Tuple, List
import aiosqlite

T = TypeVar("T")


@dataclass
class User:
    tg_id: int
    username: Optional[str]


@dataclass
class Group:
    id: int
    theme: str
    date_created: float
    date_start: float
    user_psycho: int
    user_client: int
    user_observer: int
    user_moderator: int


@dataclass
class FetchedRole:
    role: str
    user_id: int


class DB:
    def __init__(self, config: ModuleType, unique_hash: str):
        self.config = config
        self.unique_hash = unique_hash
        self.db: Optional[aiosqlite.Connection] = None

    async def connect_to_db(self):
        self.db = await aiosqlite.connect(os.path.join(self.config.BASE_DIR, f"sqlite_{self.unique_hash}.db"))
        await self.run_initial_script()

    async def run_initial_script(self, sql_file: Optional[str] = None):
        if not sql_file:
            sql_file = os.path.join(self.config.BASE_DIR, "init.sql")
        with open(sql_file, 'r') as file:
            sql_script = file.read()
        await self.db.executescript(sql_script)

    async def _fetchone(self, cursor: aiosqlite.Cursor, wrapper: T, raise_for_null=True) -> T:
        """

        :param cursor: Aiosqlite cursor
        :param wrapper: Dataclass object
        :param raise_for_null: if fetchone returns null
        :return:
        """
        result = await cursor.fetchone()
        if not result and raise_for_null:
            raise DoesNotExist(f"{wrapper.__class__.__name__} object does not exists")
        return wrapper(*result)

    async def _fetchmany(self, cursor: aiosqlite.Cursor, wrapper: T) -> List[T]:
        """
        :param cursor: Aiosqlite cursor
        :param wrapper: Dataclass object
        :return:
        """
        result = await cursor.fetchmany(size=-1)
        return [wrapper(*result_row) for result_row in result]

    async def get_user_by_tg_id(self, tg_id: int) -> Type[User]:
        async with self.db.execute("SELECT * FROM user WHERE tg_id = ?", (tg_id,)) as cur:
            return await self._fetchone(cursor=cur, wrapper=User)

    async def create_user(self, tg_id: int, username: str) -> Type[User]:
        await self.db.execute('INSERT INTO user (tg_id, username) VALUES (?, ?)', (tg_id, username))
        await self.db.commit()
        return await self.get_user_by_tg_id(tg_id)

    async def get_user_or_create(self, tg_id: int, username: str) -> tuple[Type[User], bool]:
        """
        :param tg_id: Телеграм ID
        :param username: Телеграм Username
        :return: Возращает кортеж (User, is_created: bool)
        """
        try:
            return (await self.get_user_by_tg_id(tg_id)), False
        except DoesNotExist:
            return (await self.create_user(tg_id, username)), True

    async def get_group_by_id(self, group_id: int) -> Type[Group]:
        async with self.db.execute("SELECT * FROM 'group' WHERE id = ?", (group_id,)) as cur:
            return await self._fetchone(cursor=cur, wrapper=Group)

    async def get_groups_by_user_id(self, user_id: int, reverse: bool = False) -> list[Type[Group]]:
        if not reverse:
            execution_prompt = "SELECT * FROM 'group' WHERE user_psycho = ? OR user_client = ? OR user_observer = ? OR user_moderator = ?"
            execution_format = (user_id, user_id, user_id, user_id)
        else:
            execution_prompt = "SELECT * FROM 'group' WHERE user_psycho != ? AND user_client != ? AND user_observer != ?"
            execution_format = (user_id, user_id, user_id)

        async with self.db.execute(execution_prompt, execution_format) as cur:
            return await self._fetchmany(cursor=cur, wrapper=Group)

    async def get_all_groups(self):
        async with self.db.execute("SELECT * FROM 'group'") as cur:
            return await self._fetchmany(cursor=cur, wrapper=Group)

    async def create_group(self, theme: str, date_start: float, user_moderator: int, user_psycho: Optional[int] = None,
                           user_client: Optional[int] = None, user_observer: Optional[int] = None) -> Type[Group]:
        """
        Создатель тройки может иметь как роль психолога, так и роль наблюдателя/клиента,
        так что некоторые параментры могут быть пустыми.

        Создатель является как и наблюдателем/психологом/клиентом, так и модератором!

        :param theme: Тема тройки, например "семейные разговоры"
        :param date_start: Дата старта тройки. Формат UNIX!
        :param user_moderator: ID юзера, кто создал тройку
        :param user_psycho: ID юзера, чья роль психолог
        :param user_client: ID юзера, чья роль клиент
        :param user_observer: ID юзера, чья роль смотритель
        :return:
        """
        date_created = int(time.time())
        cursor = await self.db.execute(
            'INSERT INTO "group" (theme, date_created, date_start, user_psycho, user_client, '
            'user_observer, user_moderator) VALUES (?, ?, ?, ?, ?, ?, ?)', (theme,
                                                                            date_created, date_start, user_psycho,
                                                                            user_client, user_observer, user_moderator))
        await self.db.commit()
        return await self.get_group_by_id(cursor.lastrowid)

    async def delete_group_by_id(self, group_id: int):
        sql = "DELETE FROM 'group' WHERE id = ?"
        await self.db.execute(sql, (group_id,))
        await self.db.commit()

    async def get_groups_with_free_role(self, role: str, user_id: int):

        if role == "user_any":
            sql = f"SELECT * FROM `group` WHERE (user_psycho <> {user_id} OR user_psycho IS NULL) AND (user_client <> {user_id} OR user_client IS NULL) AND (user_observer <> {user_id} OR user_observer IS NULL) AND (user_psycho IS NULL OR user_client IS NULL OR user_observer IS NULL);"

        else:
            sql = f"SELECT * FROM `group` WHERE {role} IS NULL AND (user_psycho <> {user_id} OR user_psycho IS NULL) AND (user_client <> {user_id} OR user_client IS NULL) AND (user_observer <> {user_id} OR user_observer IS NULL);"

        async with self.db.execute(sql) as cur:
            return await self._fetchmany(cursor=cur, wrapper=Group)

    async def update_group_role(self, role: str, user_id: int, group_id: int):
        query = f'UPDATE `group` SET `{role}` = ? WHERE `id`= ?;'
        await self.db.execute(query, (user_id, group_id,))
        await self.db.commit()
