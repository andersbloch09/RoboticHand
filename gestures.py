"""
Gesture definitions for the robotic hand.

Each gesture is a combination of synergy + grasp configuration.
Gestures can be tested and validated independently.
"""

from synergy import Synergy
from grasp import Grasp


class Gestures:
    """
    Library of hand gestures for testing and demonstration.
    
    Each gesture is pre-configured with:
    - Motion pattern (synergy)
    - Force profile (torque limits)
    - Timing and coordination
    """
    
    @staticmethod
    def thumbs_up():
        """
        Thumbs up gesture.
        
        - Thumb: Extended up (abducted, not fully flexed)
        - Fingers: Fully closed into a fist
        - Force: Strong grip
        """
        synergy = Synergy("thumbs_up", {
            "finger_0": 1.0,        # Index: close fast
            "finger_1": 1.0,        # Middle: close fast
            "finger_2": 1.0,        # Ring: close fast
            "finger_3": 1.0,        # Pinky: close fast
            "thumb_flexion": 0.0,   # Thumb: NOT flexed (extended)
            "thumb_abduction": 1.0, # Thumb: abducted (spread up)
        })
        
        grasp = Grasp("thumbs_up", synergy, {
            "finger_0": 0.2,
            "finger_1": 0.2,
            "finger_2": 0.2,
            "finger_3": 0.2,
            "thumb_flexion": 0.2,   # Full contraction threshold
            "thumb_abduction": 0.2, # Full contraction threshold
        })
        
        return grasp
    
    @staticmethod
    def peace_sign():
        """
        Peace sign (V-sign) gesture.
        
        - Thumb: Relaxed aside
        - Index + Middle: Extended upward
        - Ring + Pinky: Closed into palm
        - Force: Light (extended fingers)
        """
        synergy = Synergy("peace_sign", {
            "finger_0": 0.0,        # Index: NOT closed (extended)
            "finger_1": 0.0,        # Middle: NOT closed (extended)
            "finger_2": 1.0,        # Ring: close tight
            "finger_3": 1.0,        # Pinky: close tight
            "thumb_flexion": 0.3,   # Thumb: slightly flexed
            "thumb_abduction": 0.5, # Thumb: partially abducted
        })
        
        grasp = Grasp("peace_sign", synergy, {
            "finger_0": 0.2,        # Full contraction threshold
            "finger_1": 0.2,        # Full contraction threshold
            "finger_2": 0.2,
            "finger_3": 0.2,
            "thumb_flexion": 0.2,
            "thumb_abduction": 0.2,
        })
        
        return grasp
    
    @staticmethod
    def rock_sign():
        """
        Rock sign gesture (horns).
        
        - Thumb: Relaxed aside
        - Index: Extended upward
        - Middle: Relaxed
        - Ring + Pinky: Extended upward
        - Force: Light (extended fingers)
        """
        synergy = Synergy("rock_sign", {
            "finger_0": 0.0,        # Index: extended
            "finger_1": 1.0,        # Middle: closed
            "finger_2": 1.0,        # Ring: extended
            "finger_3": 0.0,        # Pinky: extended
            "thumb_flexion": 0.2,   # Thumb: slightly flexed
            "thumb_abduction": 0.8, # Thumb: spread
        })
        
        grasp = Grasp("rock_sign", synergy, {
            "finger_0": 0.2,        # Full contraction threshold
            "finger_1": 0.2,        # Full contraction threshold
            "finger_2": 0.2,        # Full contraction threshold
            "finger_3": 0.2,        # Full contraction threshold
            "thumb_flexion": 0.2,
            "thumb_abduction": 0.2,
        })
        
        return grasp
    
    @staticmethod
    def ok_sign():
        """
        OK sign gesture.
        
        - Thumb: Flexed inward
        - Index: Flexed inward (touching thumb)
        - Middle + Ring + Pinky: Extended upward
        - Force: Very light (extended fingers)
        """
        synergy = Synergy("ok_sign", {
            "finger_0": 1.0,        # Index: closed (touches thumb)
            "finger_1": 0.0,        # Middle: extended
            "finger_2": 0.0,        # Ring: extended
            "finger_3": 0.0,        # Pinky: extended
            "thumb_flexion": 1.0,   # Thumb: fully flexed
            "thumb_abduction": 0.0, # Thumb: not abducted
        })
        
        grasp = Grasp("ok_sign", synergy, {
            "finger_0": 0.2,        # Full contraction threshold
            "finger_1": 0.2,        # Full contraction threshold
            "finger_2": 0.2,        # Full contraction threshold
            "finger_3": 0.2,        # Full contraction threshold
            "thumb_flexion": 0.2,
            "thumb_abduction": 0.2,
        })
        
        return grasp
    
    @staticmethod
    def open_hand():
        """
        Open hand gesture.
        
        - All fingers: Extended flat
        - Thumb: Extended to side
        - Force: Minimal (just holding open against springs)
        """
        synergy = Synergy("open_hand", {
            "finger_0": 0.0,        # Index: extended
            "finger_1": 0.0,        # Middle: extended
            "finger_2": 0.0,        # Ring: extended
            "finger_3": 0.0,        # Pinky: extended
            "thumb_flexion": 0.0,   # Thumb: extended
            "thumb_abduction": 1.0, # Thumb: fully abducted
        })
        
        grasp = Grasp("open_hand", synergy, {
            "finger_0": 0.2,        # Full contraction threshold
            "finger_1": 0.2,
            "finger_2": 0.2,
            "finger_3": 0.2,
            "thumb_flexion": 0.2,
            "thumb_abduction": 0.2,
        })
        
        return grasp
    
    @staticmethod
    def power_fist():
        """
        Power fist (closed fist with thumb up).
        
        - All fingers: Fully closed
        - Thumb: Flexed but slightly raised
        - Force: Maximum grip strength
        """
        synergy = Synergy("power_fist", {
            "finger_0": 1.0,        # Index: close
            "finger_1": 1.0,        # Middle: close
            "finger_2": 1.0,        # Ring: close
            "finger_3": 1.0,        # Pinky: close
            "thumb_flexion": 0.7,   # Thumb: mostly flexed
            "thumb_abduction": 0.2, # Thumb: slightly spread
        })
        
        grasp = Grasp("power_fist", synergy, {
            "finger_0": 0.2,        # Full contraction threshold
            "finger_1": 0.2,
            "finger_2": 0.2,
            "finger_3": 0.2,
            "thumb_flexion": 0.2,   # Full contraction threshold
            "thumb_abduction": 0.2,
        })
        
        return grasp
    
    @staticmethod
    def point():
        """
        Pointing gesture.
        
        - Index: Extended forward (pointing)
        - Other fingers: Closed into fist
        - Thumb: Closed with fingers
        - Force: Strong grip (except index)
        """
        synergy = Synergy("point", {
            "finger_0": 0.0,        # Index: extended (pointing)
            "finger_1": 1.0,        # Middle: close
            "finger_2": 1.0,        # Ring: close
            "finger_3": 1.0,        # Pinky: close
            "thumb_flexion": 1.0,   # Thumb: close with fingers
            "thumb_abduction": 0.0,
        })
        
        grasp = Grasp("point", synergy, {
            "finger_0": 0.2,        # Full contraction threshold
            "finger_1": 0.2,
            "finger_2": 0.2,
            "finger_3": 0.2,
            "thumb_flexion": 0.2,
            "thumb_abduction": 0.2,
        })
        
        return grasp
    
    @staticmethod
    def precision_grip():
        """
        Precision grip (thumb + index pinching).
        
        - Index + Thumb: Light contact (precision pinch)
        - Other fingers: Relaxed/open
        - Force: Minimal (delicate handling)
        """
        synergy = Synergy("precision_grip", {
            "finger_0": 1.0,        # Index: slightly flexed
            "finger_1": 0.0,        # Middle: open
            "finger_2": 0.0,        # Ring: open
            "finger_3": 0.0,        # Pinky: open
            "thumb_flexion": 0.1,   # Thumb: slightly flexed
            "thumb_abduction": 0.5, # Thumb: not spread
        })
        
        grasp = Grasp("precision_grip", synergy, {
            "finger_0": 0.2,        # Full contraction threshold
            "finger_1": 0.2,
            "finger_2": 0.2,
            "finger_3": 0.2,
            "thumb_flexion": 0.2,   # Full contraction threshold
            "thumb_abduction": 0.2,
        })
        
        return grasp
    
    @staticmethod
    def get_all_gestures():
        """Return dict of all available gestures."""
        return {
            "thumbs_up": Gestures.thumbs_up(),
            "peace_sign": Gestures.peace_sign(),
            "rock_sign": Gestures.rock_sign(),
            "ok_sign": Gestures.ok_sign(),
            "open_hand": Gestures.open_hand(),
            "power_fist": Gestures.power_fist(),
            "point": Gestures.point(),
            "precision_grip": Gestures.precision_grip(),
        }
