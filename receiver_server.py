# ============================================================================
# FILE 1: receiver_server.py (Flask Server - Compatible with Flutter)
# ============================================================================

from flask import Flask, request, jsonify
import json
import threading
from datetime import datetime
import os

app = Flask(__name__)

# Global variables to store latest coordinates
latest_coordinates = {
    'latitude': None,
    'longitude': None,
    'timestamp': None,
    'accuracy': None
}

# File to store coordinates for the GUI app to read
COORDINATES_FILE = 'live_gps_coordinates.json'

def save_coordinates_to_file(lat, lon, timestamp=None, accuracy=None):
    """Save coordinates to a JSON file for the GUI app to read"""
    data = {
        'latitude': float(lat),  # Ensure it's a float
        'longitude': float(lon),  # Ensure it's a float
        'timestamp': timestamp or datetime.now().isoformat(),
        'accuracy': accuracy
    }
    
    try:
        with open(COORDINATES_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Coordinates saved: Lat={lat:.6f}, Lon={lon:.6f}")
    except Exception as e:
        print(f"❌ Error saving coordinates: {e}")

@app.route('/send-coordinates', methods=['POST'])
def receive_coordinates():
    """
    Receive GPS coordinates from Flutter app
    Expected JSON format:
    {
        "latitude": 23.7465,
        "longitude": 90.3763,
        "timestamp": "2025-06-25T10:30:00.000Z"
    }
    """
    try:
        if not request.is_json:
            return jsonify({"status": "error", "message": "Request must be JSON"}), 400
        
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        timestamp = data.get('timestamp')
        accuracy = data.get('accuracy')  # Optional
        
        # Validate required fields
        if latitude is None or longitude is None:
            return jsonify({
                "status": "error", 
                "message": "Missing 'latitude' or 'longitude' in JSON"
            }), 400
        
        # Convert to float if needed
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (ValueError, TypeError):
            return jsonify({
                "status": "error", 
                "message": "Invalid latitude or longitude format"
            }), 400
        
        # Update global coordinates
        latest_coordinates['latitude'] = latitude
        latest_coordinates['longitude'] = longitude
        latest_coordinates['timestamp'] = timestamp or datetime.now().isoformat()
        latest_coordinates['accuracy'] = accuracy
        
        # Save to file for GUI app
        save_coordinates_to_file(latitude, longitude, timestamp, accuracy)
        
        # Print to console with timestamp
        time_str = datetime.now().strftime("%H:%M:%S")
        accuracy_str = f", Accuracy: {accuracy}m" if accuracy else ""
        print(f"[{time_str}] 📍 GPS: Lat={latitude:.6f}, Lon={longitude:.6f}{accuracy_str}")
        
        return jsonify({
            "status": "success", 
            "message": "Coordinates received and saved!",
            "received_at": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"❌ Error processing coordinates: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Server error: {str(e)}"
        }), 500

@app.route('/get-coordinates', methods=['GET'])
def get_latest_coordinates():
    """Get the latest received coordinates"""
    if latest_coordinates['latitude'] is not None:
        return jsonify({
            "status": "success",
            "data": latest_coordinates
        }), 200
    else:
        return jsonify({
            "status": "error",
            "message": "No coordinates received yet"
        }), 404

@app.route('/status', methods=['GET'])
def server_status():
    """Server status and statistics"""
    file_exists = os.path.exists(COORDINATES_FILE)
    last_update = latest_coordinates.get('timestamp', 'Never')
    
    return jsonify({
        "status": "running",
        "coordinates_file_exists": file_exists,
        "last_coordinate_update": last_update,
        "latest_coordinates": latest_coordinates,
        "server_time": datetime.now().isoformat()
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check for Flutter app"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()}), 200

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with server info"""
    status = "🟢 GPS Receiver Server is running!"
    instructions = [
        "📱 Send GPS coordinates: POST /send-coordinates",
        "📍 Get latest coordinates: GET /get-coordinates", 
        "📊 Check server status: GET /status",
        "💚 Health check: GET /health"
    ]
    
    return f"{status}<br><br>" + "<br>".join(instructions), 200

if __name__ == '__main__':
    print("🚀 Starting GPS Receiver Server...")
    print(f"📂 Coordinates file: {COORDINATES_FILE}")
    print("🌐 Server available at: http://0.0.0.0:5000")
    print("📱 Flutter app should POST to: http://YOUR_COMPUTER_IP:5000/send-coordinates")
    print("=" * 70)
    
    # Run Flask server
    app.run(host='0.0.0.0', port=5000, debug=True)