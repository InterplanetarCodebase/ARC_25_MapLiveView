# 🛰️ ARC_25_MapLiveView: Live GPS Tracking Map Viewer

This project provides a complete system for visualizing real-time GPS coordinates, sent from a mobile device (e.g., a Flutter app), on a desktop map interface. It consists of two main components:

**This was tested for this flutter app done by me. Syfe Created another version of the app and it may not work with that app**

1.  **`receiver_server.py`**: A lightweight Flask web server designed to receive GPS data via HTTP POST requests.
2.  **`mapviewer.py`**: A Python Tkinter application that reads the data collected by the server and displays the location on an interactive Google Map, showing the live position and tracking path.

## ✨ Features

- **Real-Time GPS Visualization**: See location updates live on a map.
- **Web Server Receiver**: A simple Flask server to accept coordinates from any web-enabled device.
- **Path Tracking**: Displays a trail of the last known locations to visualize movement.
- **Interactive Map Controls**: Adjust zoom level and map type (Roadmap, Satellite, Terrain, Hybrid).
- **Status Dashboard**: View connection status, GPS accuracy, and last update time.
- **Compatibility**: Designed to work seamlessly with mobile applications (like Flutter) that can send HTTP requests.
- **Standalone**: The server and viewer are independent and communicate via a local JSON file, making the system robust.

## ⚙️ How It Works

The data flows through the system in a simple, effective sequence:

1.  **Mobile App (Client)**: A GPS-enabled device (e.g., a smartphone running a Flutter app) periodically sends its `latitude`, `longitude`, `timestamp`, and `accuracy` to the Flask server in a JSON format.
2.  **Flask Server (`receiver_server.py`)**: The server listens for incoming POST requests on the `/send-coordinates` endpoint. When it receives data, it saves it to a local file: `live_gps_coordinates.json`.
3.  **Map Viewer (`mapviewer.py`)**: The desktop application continuously monitors the `live_gps_coordinates.json` file for changes. When new data is detected, it updates the map to show the new location and redraws the tracking path.

```
+--------------+        HTTP POST       +---------------------+       Writes       +------------------+
|              |  (JSON with lat/lon)   |                     |         To         |                  |
|  Mobile App  +----------------------->|  receiver_server.py |------------------->| live_gps.json    |
|   (Flutter)  |                        |    (Flask Server)   |                    |                  |
+--------------+                        +---------------------+                    +--------+---------+
                                                                                            |
                                                                                            | Watches File
                                                                                            |
                                                                                    +-------+----------+
                                                                                    |                  |
                                                                                    |  mapviewer.py    |
                                                                                    | (Desktop Viewer) |
                                                                                    +------------------+
```

## 🚀 Getting Started

Follow these steps to get the system up and running on your local machine.

### Prerequisites

- Python 3.x
- A Google account to generate a Google Maps API key.

### 1. Clone the Repository

```bash
git clone [https://github.com/InterplanetarCodebase/ARC_25_MapLiveView.git](https://github.com/InterplanetarCodebase/ARC_25_MapLiveView.git)
cd ARC_25_MapLiveView
```

### 2. Install Dependencies

All the required Python packages are listed in `requirements.txt`. Install them using pip:

```bash
pip install -r requirements.txt
```

### 3. Configure Google Maps API Key

The map viewer uses the Google Static Maps API to display the map. You must provide your own API key.

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project or select an existing one.
3.  Enable the **"Maps Static API"**.
4.  Create an API key from the "Credentials" page.
5.  Open the `mapviewer.py` file and replace the placeholder text with your actual API key:

    ```python
    # in mapviewer.py
    class LiveGPSMapsViewer:
        def __init__(self):
            # IMPORTANT: Replace with your Google Maps API key
            self.api_key = "YOUR_REAL_API_KEY_GOES_HERE"
    ```

    **⚠️ Important**: Keep your API key private. Do not commit it to a public repository.

## USAGE

To run the system, you need to start both the server and the map viewer.

### Step 1: Run the Receiver Server

Open a terminal and run the Flask server. This will start a web server listening for GPS data.

```bash
python receiver_server.py
```

You should see output indicating the server is running on `http://0.0.0.0:5000`.

### Step 2: Run the Map Viewer

Open a **second terminal** and run the Tkinter map viewer application.

```bash
python mapviewer.py
```

The desktop application window will appear, initially centered on the default coordinates (Dhaka).

### Step 3: Send GPS Data to the Server

Now, you need to send GPS data from your mobile app or another tool (like `curl` or Postman) to the server.

- **Endpoint**: `http://YOUR_COMPUTER_IP:5000/send-coordinates`
- **Method**: `POST`
- **Body (JSON)**:

  ```json
  {
    "latitude": 23.7465,
    "longitude": 90.3763,
    "accuracy": 10.5,
    "timestamp": "2025-06-25T10:30:00.000Z"
  }
  ```

You can find your computer's local IP address by running `ipconfig` (Windows) or `ifconfig`/`ip addr` (macOS/Linux).

#### Example using `curl`:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"latitude": 23.8103, "longitude": 90.4125, "accuracy": 5}' [http://192.168.1.101:5000/send-coordinates](http://192.168.1.101:5000/send-coordinates)
```

As soon as you send data, the server will save it, and the map viewer will automatically update to show the new location.

## 🌐 Server API Endpoints

The `receiver_server.py` provides the following endpoints:

- `POST /send-coordinates`: The main endpoint for receiving GPS data.
- `GET /get-coordinates`: Returns the last received GPS coordinates in JSON format.
- `GET /status`: Provides a status report of the server, including the last update time.
- `GET /health`: A simple health check endpoint that returns a `200 OK` if the server is running.
