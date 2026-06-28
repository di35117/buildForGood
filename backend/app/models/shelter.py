from sqlalchemy import Column, Integer, String
from geoalchemy2 import Geometry
from app.db.base_class import Base

class Shelter(Base):
    """
    [P0] Module 2: Shelter & NGO Directory.
    Stores safe houses and uses PostGIS for location-based filtering.
    """
    __tablename__ = "shelters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    organization_type = Column(String, default="NGO")  # e.g., NGO, Women's Shelter, Police Station
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=True)
    location = Column(Geometry('POINT', srid=4326), nullable=False)