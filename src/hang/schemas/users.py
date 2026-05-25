from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from datetime import datetime, date
from typing import List, Optional
from enum import Enum


class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class InterestedIn(str, Enum):
    male = "male"
    female = "female"
    everyone = "everyone"


class Interests(str, Enum):
    sports = "sports"
    outdoor = "outdoor"
    fitness = "fitness"
    gaming = "gaming"
    music = "music"
    movies = "movies"
    travel = "travel"
    food = "food"
    cooking = "cooking"
    reading = "reading"
    art = "art"
    photography = "photography"
    tech = "tech"
    fashion = "fashion"
    nightlife = "nightlife"
    pets = "pets"
    nature = "nature"
    cars = "cars"


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    birthdate: date
    bio: str
    gender: Gender
    country: str
    interested_in: InterestedIn
    interests: List[Interests]
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserImageResponse(BaseModel):
    image_id: int
    image_key: str
    position: int

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: EmailStr
    country: str
    birthdate: date
    bio: str
    gender: Gender
    interested_in: InterestedIn
    interests: List[Interests]

    images: List[UserImageResponse] = Field(default_factory=list)

    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("interests", mode="before")
    def convert_interests(cls, v):
        if v is None:
            return []
        return [Interests(i) if not isinstance(i, Interests) else i for i in v]

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class UserOnboardResponse(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    country: str
    birthdate: Optional[date] = None
    bio: Optional[str] = None
    gender: Gender
    interested_in: InterestedIn
    interests: List[Interests]

    images: List[UserImageResponse] = Field(default_factory=list)

    @field_validator("interests", mode="before")
    def convert_interests(cls, v):
        if v is None:
            return []
        return [Interests(i) if not isinstance(i, Interests) else i for i in v]

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class UserSwipeProfile(BaseModel):
    user_id: int
    first_name: str
    bio: str
    interests: List[Interests]
    gender: Gender
    images: List[UserImageResponse] = Field(default_factory=list)

    @field_validator("interests", mode="before")
    def convert_interests(cls, v):
        if v is None:
            return []
        return [Interests(i) if not isinstance(i, Interests) else i for i in v]

    model_config = ConfigDict(from_attributes=True)


class ImageUpdate(BaseModel):
    image_id: int
    position: Optional[int] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    birthdate: Optional[date] = None
    country: Optional[str] = None
    gender: Optional[Gender] = None
    bio: Optional[str] = None
    interested_in: Optional[InterestedIn] = None
    interests: Optional[List[Interests]] = None

    deleted_images: Optional[List[int]] = []
    images: Optional[List[ImageUpdate]] = []


class BlockUserCreate(BaseModel):
    blocked_user_id: int


class ReportUserCreate(BaseModel):
    reported_user_id: int
    reason: str = Field(..., max_length=100)
    message: Optional[str] = Field(None, max_length=500)
