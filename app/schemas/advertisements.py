from pydantic import BaseModel


class AdvertisementCreate(BaseModel):
    """
    Schema for creating a new advertisement.

    Attributes:
        title (str): The title of the advertisement.
        description (str): A detailed description of the advertisement.
        media (str): The media type used in the advertisement (e.g., image, video).
        target_audience (str): The intended audience for the advertisement.
    """

    title: str
    description: str
    media: str
    target_audience: str


class AdvertisementUpdate(BaseModel):
    """
    Schema for updating an existing advertisement.

    All fields are optional since updates can be partial.
    """

    title: str | None = None
    description: str | None = None
    media: str | None = None
    target_audience: str | None = None


class AdvertisementResponse(BaseModel):
    """
    Schema for advertisement response.

    This schema represents how advertisement data is returned from the API.
    It includes all fields from the model including the generated ID and user_id.

    Attributes:
        id (str): The unique identifier of the advertisement.
        title (str): The title of the advertisement.
        description (str): A detailed description of the advertisement.
        media (str): The media type used in the advertisement.
        target_audience (str): The intended audience for the advertisement.
        user_id (str): The ID of the user who created the advertisement.
    """

    id: str
    title: str
    description: str
    media: str
    target_audience: str
    user_id: str

    class Config:
        from_attributes = True
