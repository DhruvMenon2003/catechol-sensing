import json
import os
from datetime import datetime

PEAK_CURRENT_FILE = "anodic_peak_data.json"

def save_anodic_peak_current(peak_anodic_current):
    """
    Save the anodic peak current value to a JSON file for later retrieval.
    
    Parameters:
    -----------
    peak_anodic_current : float
        The anodic peak current value in µA
    
    Returns:
    --------
    bool
        True if save was successful, False otherwise
    """
    try:
        # Create data structure with timestamp for tracking
        peak_data = {
            "anodic_peak_current_uA": float(peak_anodic_current),
            "timestamp": datetime.now().isoformat(),
            "unit": "µA"
        }
        
        # Write to JSON file
        with open(PEAK_CURRENT_FILE, "w") as f:
            json.dump(peak_data, f, indent=4)
        
        print(f"✓ Anodic peak current saved: {peak_anodic_current:.6f} µA")
        return True
        
    except Exception as e:
        print(f"✗ Error saving anodic peak current: {e}")
        return False


def load_anodic_peak_current():
    """
    Load the previously saved anodic peak current value from the JSON file.
    
    Returns:
    --------
    float or None
        The anodic peak current value in µA, or None if file doesn't exist/error
    """
    try:
        if not os.path.exists(PEAK_CURRENT_FILE):
            print(f"⚠ Peak current file not found: {PEAK_CURRENT_FILE}")
            return None
        
        with open(PEAK_CURRENT_FILE, "r") as f:
            peak_data = json.load(f)
        
        peak_current = peak_data.get("anodic_peak_current_uA")
        timestamp = peak_data.get("timestamp", "Unknown")
        
        print(f"✓ Anodic peak current loaded: {peak_current:.6f} µA (from {timestamp})")
        return float(peak_current)
        
    except Exception as e:
        print(f"✗ Error loading anodic peak current: {e}")
        return None


def get_peak_current_data():
    """
    Get the full peak current data dictionary including metadata.
    
    Returns:
    --------
    dict or None
        Dictionary with peak current data and metadata, or None if unavailable
    """
    try:
        if not os.path.exists(PEAK_CURRENT_FILE):
            return None
        
        with open(PEAK_CURRENT_FILE, "r") as f:
            return json.load(f)
            
    except Exception as e:
        print(f"✗ Error reading peak current data: {e}")
        return None


# Example usage (uncomment to test):
# if __name__ == "__main__":
#     # Save example peak current value
#     save_anodic_peak_current(42.567890)
#     
#     # Load the saved value
#     loaded_value = load_anodic_peak_current()
#     
#     # Get full data
#     full_data = get_peak_current_data()
#     print(f"Full data: {full_data}")
