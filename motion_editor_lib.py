"""Motion library backend for saving/loading motions."""
import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

MOTIONS_DIR = "user_motions"
os.makedirs(MOTIONS_DIR, exist_ok=True)


@dataclass
class MotionMetadata:
    """Metadata for a saved motion."""
    name: str
    duration: float
    easing: str
    repeat: int
    loop: bool
    description: str = ""


class MotionLibrary:
    """Manages saving/loading motions from disk."""
    
    def __init__(self, directory=MOTIONS_DIR):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
    
    def save_motion(self, name: str, keyframes: List[Tuple[float, Dict]], 
                   metadata: MotionMetadata) -> bool:
        """Save motion to JSON file."""
        try:
            motion_data = {
                "name": metadata.name,
                "duration": metadata.duration,
                "easing": metadata.easing,
                "repeat": metadata.repeat,
                "loop": metadata.loop,
                "description": metadata.description,
                "keyframes": keyframes,
            }
            
            filepath = os.path.join(self.directory, f"{name}.json")
            with open(filepath, "w") as f:
                json.dump(motion_data, f, indent=2)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save motion: {e}")
            return False
    
    def load_motion(self, name: str) -> Optional[Tuple[List, MotionMetadata]]:
        """Load motion from JSON file."""
        try:
            filepath = os.path.join(self.directory, f"{name}.json")
            with open(filepath, "r") as f:
                data = json.load(f)
            
            keyframes = data["keyframes"]
            metadata = MotionMetadata(
                name=data["name"],
                duration=data["duration"],
                easing=data["easing"],
                repeat=data["repeat"],
                loop=data["loop"],
                description=data.get("description", ""),
            )
            return keyframes, metadata
        except Exception as e:
            print(f"[ERROR] Failed to load motion: {e}")
            return None
    
    def list_motions(self) -> List[str]:
        """List all saved motion names."""
        try:
            motions = [f[:-5] for f in os.listdir(self.directory) if f.endswith(".json")]
            return sorted(motions)
        except:
            return []
    
    def delete_motion(self, name: str) -> bool:
        """Delete saved motion."""
        try:
            filepath = os.path.join(self.directory, f"{name}.json")
            os.remove(filepath)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to delete motion: {e}")
            return False


class CalibrationLoader:
    """Load calibration data from calibration.json."""
    
    @staticmethod
    def load() -> Dict:
        """Load calibration limits for all digits."""
        if os.path.exists("calibration.json"):
            try:
                with open("calibration.json", "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed to load calibration: {e}")
        return {}
