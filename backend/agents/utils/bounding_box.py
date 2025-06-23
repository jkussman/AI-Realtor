from pydantic import BaseModel
from typing import Optional

class BoundingBox(BaseModel):
    """Represents a geographic bounding box with north, south, east, and west coordinates."""
    north: float
    south: float
    east: float
    west: float
    
    def to_dict(self) -> dict:
        """Convert the bounding box to a dictionary."""
        return {
            "north": self.north,
            "south": self.south,
            "east": self.east,
            "west": self.west
        } 