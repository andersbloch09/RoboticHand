class Synergy:
    def __init__(self, name, digit_gains):
        self.name = name
        self.digit_gains = digit_gains
    
    def activate(self, fingers_dict, thumb, index_abduction=None):
        # Command all fingers with their gains
        for finger_name, finger in fingers_dict.items():
            if finger_name in self.digit_gains:
                gain = self.digit_gains[finger_name]
                finger.command(gain)
        
        # Command thumb flexion with its gain
        thumb_flex_gain = self.digit_gains.get("thumb_flexion", 0.0)
        thumb_abd_gain = self.digit_gains.get("thumb_abduction", 0.0)
        thumb.command(thumb_flex_gain, thumb_abd_gain)
        
        # Command index abduction if present
        if index_abduction and "index_abduction" in self.digit_gains:
            gain = self.digit_gains["index_abduction"]
            index_abduction.command(gain)
    
    def __repr__(self):
        return f"Synergy(name='{self.name}', gains={self.digit_gains})"
