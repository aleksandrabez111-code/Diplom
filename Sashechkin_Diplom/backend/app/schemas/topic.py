from pydantic import BaseModel, Field, model_validator

from app.schemas.user import UserShort


class TopicPublic(BaseModel):
    id: int
    name: str

    model_config = {'from_attributes': True}


class TopicCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    is_active: bool = True
    specialist_ids: list[int] = Field(default_factory=list)
    specialist_id: int | None = None

    @model_validator(mode='after')
    def normalize_specialists(self) -> 'TopicCreate':
        if self.specialist_id is not None and self.specialist_id not in self.specialist_ids:
            self.specialist_ids.append(self.specialist_id)
        self.specialist_ids = sorted(set(self.specialist_ids))
        return self


class TopicUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    is_active: bool | None = None
    specialist_ids: list[int] | None = None
    specialist_id: int | None = None

    @model_validator(mode='after')
    def normalize_specialists(self) -> 'TopicUpdate':
        if self.specialist_ids is not None:
            values = list(self.specialist_ids)
            if self.specialist_id is not None and self.specialist_id not in values:
                values.append(self.specialist_id)
            self.specialist_ids = sorted(set(values))
        elif self.specialist_id is not None:
            self.specialist_ids = [self.specialist_id]
        return self


class TopicResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    specialists: list[UserShort] = Field(default_factory=list)
    specialist: UserShort | None = None

    model_config = {'from_attributes': True}
