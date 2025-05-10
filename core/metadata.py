import json
import datetime

def generate_metadata(subject_id, session_id, frame_count, camera_settings):
    return {
        "subject_id": subject_id,
        "session_id": session_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "frame_count": frame_count,
        "camera_settings": camera_settings
    }

def save_metadata_to_json(metadata, filename):
    with open(filename, 'w') as f:
        json.dump(metadata, f, indent=4)