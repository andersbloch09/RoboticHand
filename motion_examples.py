"""
Example motions for the robotic hand.

Demonstrates how to use the motion system for complex coordinated movements.
"""

from motion import Motion, MotionSequence, EasingFunction


# ============================================================================
# EXAMPLE 1: Index Finger Circular Motion
# ============================================================================
# The index finger performs a circular motion by coordinating:
# - Flexion (opening/closing)
# - Abduction (left/right movement)
# 
# Normalized positions: 0.0 = open/center, 1.0 = closed/extreme

index_circle = Motion(
    name="index_circle",
    keyframes=[
        # (time, {digit_name: normalized_position})
        
        # Start: flexed, centered
        (0.0, {"finger_0": 1.0, "finger_0_abd": 0.5}),
        
        # Quarter circle: opening, moving right
        (0.5, {"finger_0": 0.5, "finger_0_abd": 1.0}),
        
        # Half circle: fully open, centered
        (1.0, {"finger_0": 0.0, "finger_0_abd": 0.5}),
        
        # Three-quarter circle: closing, moving left
        (1.5, {"finger_0": 0.5, "finger_0_abd": 0.0}),
        
        # Back to start: flexed, centered
        (2.0, {"finger_0": 1.0, "finger_0_abd": 0.5}),
    ],
    duration=2.0,
    easing="ease_in_out_cubic",
    repeat=1,
)

# Looping version that repeats forever
index_circle_loop = Motion(
    name="index_circle_loop",
    keyframes=[
        (0.0, {"finger_0": 1.0, "finger_0_abd": 0.5}),
        (0.5, {"finger_0": 0.5, "finger_0_abd": 1.0}),
        (1.0, {"finger_0": 0.0, "finger_0_abd": 0.5}),
        (1.5, {"finger_0": 0.5, "finger_0_abd": 0.0}),
        (2.0, {"finger_0": 1.0, "finger_0_abd": 0.5}),
    ],
    duration=2.0,
    easing="ease_in_out_cubic",
    loop=True,  # Repeat forever
)


# ============================================================================
# EXAMPLE 2: Wave Motion (All Fingers)
# ============================================================================
# Fingers open sequentially from index to pinky (like a wave)

wave_motion = Motion(
    name="wave",
    keyframes=[
        # Start: all closed
        (0.0, {
            "finger_0": 1.0,
            "finger_1": 1.0,
            "finger_2": 1.0,
            "finger_3": 1.0,
        }),
        
        # Index opens
        (0.3, {
            "finger_0": 0.0,
            "finger_1": 1.0,
            "finger_2": 1.0,
            "finger_3": 1.0,
        }),
        
        # Index closes, middle opens
        (0.6, {
            "finger_0": 1.0,
            "finger_1": 0.0,
            "finger_2": 1.0,
            "finger_3": 1.0,
        }),
        
        # Middle closes, ring opens
        (0.9, {
            "finger_0": 1.0,
            "finger_1": 1.0,
            "finger_2": 0.0,
            "finger_3": 1.0,
        }),
        
        # Ring closes, pinky opens
        (1.2, {
            "finger_0": 1.0,
            "finger_1": 1.0,
            "finger_2": 1.0,
            "finger_3": 0.0,
        }),
        
        # Pinky closes
        (1.5, {
            "finger_0": 1.0,
            "finger_1": 1.0,
            "finger_2": 1.0,
            "finger_3": 1.0,
        }),
    ],
    duration=1.5,
    easing="ease_in_out_cubic",
    repeat=1,
)


# ============================================================================
# EXAMPLE 3: Thumb Abduction (Thumbs Up variant)
# ============================================================================
# Thumb spreads out and comes back in

thumb_spread = Motion(
    name="thumb_spread",
    keyframes=[
        # Start: centered
        (0.0, {"thumb_abduction": 0.5}),
        
        # Spread out
        (0.5, {"thumb_abduction": 1.0}),
        
        # Back to center
        (1.0, {"thumb_abduction": 0.5}),
    ],
    duration=1.0,
    easing="ease_in_out_cubic",
    repeat=2,  # Do it twice
)


# ============================================================================
# EXAMPLE 4: Sequential Motion Sequence
# ============================================================================
# Multiple motions that play one after another

gesture_sequence = MotionSequence(
    name="sequence_example",
    motions=[
        # First: all fingers open smoothly
        Motion(
            name="open_all",
            keyframes=[
                (0.0, {"finger_0": 1.0, "finger_1": 1.0, "finger_2": 1.0, "finger_3": 1.0}),
                (1.0, {"finger_0": 0.0, "finger_1": 0.0, "finger_2": 0.0, "finger_3": 0.0}),
            ],
            duration=1.0,
            easing="ease_out_cubic",
        ),
        
        # Then: thumb spreads while fingers stay open
        Motion(
            name="thumb_spread_seq",
            keyframes=[
                (0.0, {"thumb_abduction": 0.5}),
                (0.5, {"thumb_abduction": 1.0}),
                (1.0, {"thumb_abduction": 0.5}),
            ],
            duration=1.0,
            easing="ease_in_out_cubic",
        ),
        
        # Finally: close all fingers
        Motion(
            name="close_all",
            keyframes=[
                (0.0, {"finger_0": 0.0, "finger_1": 0.0, "finger_2": 0.0, "finger_3": 0.0}),
                (1.0, {"finger_0": 1.0, "finger_1": 1.0, "finger_2": 1.0, "finger_3": 1.0}),
            ],
            duration=1.0,
            easing="ease_in_cubic",
        ),
    ],
    parallel=False,  # Play sequentially
)


# ============================================================================
# EXAMPLE 5: Parallel Motion (Multiple Movements Simultaneously)
# ============================================================================
# All fingers AND thumb move at the same time

parallel_sequence = MotionSequence(
    name="parallel_example",
    motions=[
        # Fingers spread open
        Motion(
            name="fingers_open",
            keyframes=[
                (0.0, {"finger_0": 1.0, "finger_1": 1.0, "finger_2": 1.0, "finger_3": 1.0}),
                (1.0, {"finger_0": 0.0, "finger_1": 0.0, "finger_2": 0.0, "finger_3": 0.0}),
            ],
            duration=1.0,
            easing="ease_out_sine",
        ),
        
        # Thumb spreads at same time
        Motion(
            name="thumb_spreads",
            keyframes=[
                (0.0, {"thumb_abduction": 0.5}),
                (1.0, {"thumb_abduction": 1.0}),
            ],
            duration=1.0,
            easing="ease_out_sine",
        ),
    ],
    parallel=True,  # Run simultaneously
)


# ============================================================================
# EXAMPLE 6: Smooth Tremor (Vibration)
# ============================================================================
# Rapid flexion/extension for tremor-like motion

tremor = Motion(
    name="tremor",
    keyframes=[
        (0.0, {"finger_0": 0.5}),
        (0.05, {"finger_0": 0.6}),
        (0.1, {"finger_0": 0.4}),
        (0.15, {"finger_0": 0.6}),
        (0.2, {"finger_0": 0.4}),
        (0.25, {"finger_0": 0.6}),
        (0.3, {"finger_0": 0.4}),
        (0.35, {"finger_0": 0.55}),
        (0.4, {"finger_0": 0.5}),
    ],
    duration=0.4,
    easing="linear",  # No easing for smooth oscillation
    repeat=1,
)


# ============================================================================
# USAGE IN MAIN CODE
# ============================================================================
# In your main program, use like this:
#
#   from motion_examples import index_circle, wave_motion
#   
#   # Play a single motion
#   hand.motion_player.play_motion(index_circle)
#   
#   # Or play a sequence
#   hand.motion_player.play_sequence(gesture_sequence)
#   
#   # In the control loop, motion_player.update(dt) is already called
#   # in hand.update(dt), so motions will execute automatically


# ============================================================================
# HOW TO CREATE YOUR OWN MOTIONS
# ============================================================================
# 
# 1. Define keyframes as list of (time_seconds, {digit_name: normalized_pos})
#    - time: 0.0 to duration seconds
#    - digit_name: "finger_0", "finger_1", "finger_2", "finger_3",
#                  "thumb_flexion", "thumb_abduction"
#    - normalized_pos: 0.0 (open) to 1.0 (closed)
#
# 2. For index finger abduction, use "finger_0_abd" pattern
#    (requires calibration support in motion_player)
#
# 3. Available easing functions:
#    - "linear" - constant speed
#    - "ease_in_quad", "ease_out_quad", "ease_in_out_quad"
#    - "ease_in_cubic", "ease_out_cubic", "ease_in_out_cubic"
#    - "ease_in_sine", "ease_out_sine", "ease_in_out_sine"
#
# 4. Set repeat=N for N repetitions, or loop=True for infinite
#
# 5. Combine motions with MotionSequence for complex gestures


def get_all_example_motions():
    """Return all example motions as a dict."""
    return {
        "index_circle": index_circle,
        "index_circle_loop": index_circle_loop,
        "wave": wave_motion,
        "thumb_spread": thumb_spread,
        "tremor": tremor,
    }


def get_all_example_sequences():
    """Return all example sequences as a dict."""
    return {
        "sequence_example": gesture_sequence,
        "parallel_example": parallel_sequence,
    }
