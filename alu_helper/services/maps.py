from alu_helper.database import connect
from pydantic import BaseModel


class Map(BaseModel):
    id: int
    name: str

class MapsRepository:
    @staticmethod
    def parse(row):
        return Map(**row) if row else None

    def add(self, item: Map) -> int:
        with connect() as conn:
            conn.execute("INSERT OR IGNORE INTO maps(name) VALUES (:name)", item.model_dump())
            return conn.execute("SELECT id FROM maps WHERE name = :name LIMIT 1", item.model_dump()).fetchone()[0]


    def get(self, name: str):
        with connect() as conn:
            row = conn.execute("SELECT * FROM maps WHERE name = :name LIMIT 1", {"name": name}).fetchone()
            return self.parse(row)

    def get_all(self, query: str):
        with connect() as conn:
            sql = "SELECT * FROM maps"
            params = {}

            if query:
                sql += " WHERE name LIKE :query"
                params = {"query": f"%{query}%"}

            rows = conn.execute(sql + " ORDER BY name LIMIT 100", params).fetchall()
            return [self.parse(row) for row in rows]

    def update(self, item: Map):
        with connect() as conn:
            conn.execute("UPDATE maps SET name = :name WHERE id = :id", item.model_dump())

    def get_by_ids(self, maps_ids):
        ids = ", ".join(str(id) for id in maps_ids)

        with connect() as conn:
            rows = conn.execute(f"SELECT * FROM maps WHERE id in ({ids})").fetchall()
            return [self.parse(row) for row in rows]


class MapsService:
    def __init__(self, repo: MapsRepository):
        self.repo = repo

    def add(self, item: Map) -> int:
        return self.repo.add(item)

    def get_id_by_name(self, name: str) -> int:
        return self.add(Map(id=0, name=name))

    def get_all(self, query: str = ""):
        return self.repo.get_all(query.strip())

    def update(self, item: Map):
        self.repo.update(item)

    def get_by_ids(self, maps_ids: set[int]) -> dict[int, Map]:
        if not maps_ids:
            return dict()
        items = self.repo.get_by_ids(maps_ids)
        return {m.id: m for m in items}
