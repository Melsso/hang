from pydantic import BaseModel, EmailStr, Field
import pycountry
from datetime import timezone, datetime, date
from typing import List
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


class User(BaseModel):
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

    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("country")
    def validate_country(cls, v):
        if not pycountry.countries.get(alpha_2=v):
            raise ValueError(f"Invalid country code: {v}")
        return v


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    country: str
    birthdate: date
    bio: str
    gender: Gender
    interested_in: InterestedIn
    interests: List[Interests]


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

    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None
    interested_in: InterestedIn | None = None
    interests: List[Interests] | None = None