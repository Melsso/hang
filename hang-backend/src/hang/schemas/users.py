from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    ConfigDict,
    AfterValidator,
    StringConstraints,
)
from datetime import date
from typing import List, Optional, Annotated
from enum import Enum

import pycountry


VALID_COUNTRIES = {c.alpha_2 for c in pycountry.countries}


def _check_country(v: str) -> str:
    v = v.upper()
    if v not in VALID_COUNTRIES:
        raise ValueError("Unknown country code")
    return v


CountryCode = Annotated[str, AfterValidator(_check_country)]
Name = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)
]
Bio = Annotated[str, StringConstraints(max_length=500)]


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
    first_name: Name
    last_name: Name
    email: EmailStr
    birthdate: date
    bio: Bio
    gender: Gender
    country: CountryCode
    interested_in: InterestedIn
    interests: List[Interests] = Field(max_length=len(Interests))
    password: str = Field(min_length=8, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserImageResponse(BaseModel):
    image_id: int
    image_key: str
    position: int
    image_url: Optional[str] = ""

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: EmailStr
    country: str
    birthdate: Optional[date] = None
    bio: str
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
    first_name: Optional[Name] = None
    last_name: Optional[Name] = None
    country: Optional[CountryCode] = None
    bio: Optional[Bio] = None
    birthdate: Optional[date] = None
    email: Optional[EmailStr] = None
    gender: Optional[Gender] = None
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


class UserStateResponse(BaseModel):
    authenticated: bool
    user_id: Optional[int]
    onboarding_required: bool
