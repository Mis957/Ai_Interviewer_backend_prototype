from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id_val: str) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == id_val).first()

    def get_all(self, limit: int = 100) -> List[ModelType]:
        return self.db.query(self.model).limit(limit).all()

    def add(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id_val: str) -> bool:
        obj = self.get_by_id(id_val)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False
