# ============================================================================
# FILE 2: live_gps_maps_viewer.py (Enhanced Maps Viewer)
# ============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
from PIL import Image, ImageTk
from io import BytesIO
import time
import json
import os
from datetime import datetime

class LiveGPSMapsViewer:
    def __init__(self):
        # IMPORTANT: Replace with your Google Maps API key
        self.api_key = "INSERT_YOUR_GOOGLE_MAPS_API_KEY_HERE"
        
        # GPS data file (matches Flask server)
        self.gps_file = 'live_gps_coordinates.json'
        
        # Default coordinates (Dhaka, Bangladesh)
        self.latitude = 23.7465
        self.longitude = 90.3763
        self.location_name = "Waiting for GPS data..."
        self.accuracy = None
        self.last_update = None
        
        # Live GPS settings
        self.live_gps_enabled = False
        self.gps_check_interval = 1.5  # Check every 1.5 seconds
        self.gps_thread = None
        
        # Map settings
        self.zoom_level = 17  # Higher zoom for precise tracking
        self.map_size = "640x640"
        self.map_type = "roadmap"
        self.scale = 2
        
        # Location history for path tracking
        self.location_history = []
        self.max_history = 25
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the GUI interface"""
        # Main window
        self.root = tk.Tk()
        self.root.title("🛰️ Live GPS Maps Viewer - Flutter Compatible")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f5f5f5')
        self.root.minsize(1200, 800)
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === GPS STATUS PANEL ===
        gps_frame = ttk.LabelFrame(main_frame, text="🛰️ Live GPS Status", padding=10)
        gps_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Status row
        status_row = ttk.Frame(gps_frame)
        status_row.pack(fill=tk.X, pady=(0, 10))
        
        self.gps_status_label = ttk.Label(status_row, text="🔴 Waiting for GPS", 
                                         font=('Arial', 12, 'bold'), foreground='red')
        self.gps_status_label.pack(side=tk.LEFT)
        
        # Controls
        controls_row = ttk.Frame(status_row)
        controls_row.pack(side=tk.RIGHT)
        
        self.live_gps_var = tk.BooleanVar()
        ttk.Checkbutton(controls_row, text="🔄 Enable Live Tracking", 
                       variable=self.live_gps_var,
                       command=self.toggle_live_gps).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_row, text="📂 Check GPS File", 
                  command=self.check_gps_file).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_row, text="📡 Test Server", 
                  command=self.test_server_connection).pack(side=tk.LEFT, padx=5)
        
        # GPS info display
        info_frame = ttk.Frame(gps_frame)
        info_frame.pack(fill=tk.X)
        
        # Create info labels
        self.create_info_labels(info_frame)
        
        # === MAP CONTROLS ===
        control_frame = ttk.LabelFrame(main_frame, text="🎛️ Map Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        controls_container = ttk.Frame(control_frame)
        controls_container.pack(fill=tk.X)
        
        # Zoom control
        zoom_frame = ttk.Frame(controls_container)
        zoom_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(zoom_frame, text="Zoom:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.zoom_var = tk.IntVar(value=self.zoom_level)
        zoom_scale = ttk.Scale(zoom_frame, from_=1, to=20, orient=tk.HORIZONTAL, 
                              variable=self.zoom_var, length=200)
        zoom_scale.pack(side=tk.LEFT, padx=10)
        ttk.Label(zoom_frame, textvariable=self.zoom_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        # Map type
        type_frame = ttk.Frame(controls_container)
        type_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(type_frame, text="Type:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.map_type_var = tk.StringVar(value=self.map_type)
        ttk.Combobox(type_frame, textvariable=self.map_type_var,
                    values=["roadmap", "satellite", "terrain", "hybrid"],
                    state="readonly", width=10).pack(side=tk.LEFT, padx=10)
        
        # Action buttons
        buttons_frame = ttk.Frame(controls_container)
        buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(buttons_frame, text="🔄 Update Map", 
                  command=self.update_map).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🗑️ Clear Path", 
                  command=self.clear_history).pack(side=tk.LEFT, padx=5)
        
        # === MAP DISPLAY ===
        map_frame = ttk.LabelFrame(main_frame, text="🗺️ Live GPS Map", padding=5)
        map_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(map_frame, bg='white', relief=tk.SUNKEN, bd=2)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Enable Live Tracking to start")
        ttk.Label(main_frame, textvariable=self.status_var, 
                 relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X, pady=(5, 0))
        
        # Initialize
        self.update_map()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Auto-check for GPS file
        self.root.after(2000, self.auto_check_gps)
        
    def create_info_labels(self, parent):
        """Create GPS information labels"""
        ttk.Label(parent, text="📍 Location:", font=('Arial', 11, 'bold')).pack(anchor=tk.W)
        self.location_info_label = ttk.Label(parent, text=self.location_name, font=('Arial', 10))
        self.location_info_label.pack(anchor=tk.W)
        
        self.coords_info_label = ttk.Label(parent, 
                                          text=f"Coordinates: {self.latitude:.6f}, {self.longitude:.6f}", 
                                          font=('Arial', 10))
        self.coords_info_label.pack(anchor=tk.W)
        
        self.accuracy_label = ttk.Label(parent, text="Accuracy: Unknown", font=('Arial', 10))
        self.accuracy_label.pack(anchor=tk.W)
        
        self.last_update_label = ttk.Label(parent, text="Last Update: Never", font=('Arial', 10))
        self.last_update_label.pack(anchor=tk.W)
    
    def toggle_live_gps(self):
        """Toggle live GPS tracking"""
        self.live_gps_enabled = self.live_gps_var.get()
        
        if self.live_gps_enabled:
            self.start_gps_monitoring()
        else:
            self.stop_gps_monitoring()
    
    def start_gps_monitoring(self):
        """Start GPS monitoring thread"""
        if self.gps_thread and self.gps_thread.is_alive():
            return
        
        self.gps_thread = threading.Thread(target=self.gps_monitoring_loop, daemon=True)
        self.gps_thread.start()
        self.gps_status_label.config(text="🟡 Monitoring Active", foreground='orange')
        self.status_var.set("GPS monitoring started - waiting for Flutter data...")
    
    def stop_gps_monitoring(self):
        """Stop GPS monitoring"""
        self.live_gps_enabled = False
        self.gps_status_label.config(text="🔴 Monitoring Stopped", foreground='red')
        self.status_var.set("GPS monitoring stopped")
    
    def gps_monitoring_loop(self):
        """Background GPS monitoring loop"""
        consecutive_failures = 0
        
        while self.live_gps_enabled:
            try:
                if self.read_gps_coordinates():
                    consecutive_failures = 0
                    # Update GUI in main thread
                    self.root.after(0, self.update_gps_display)
                    self.root.after(0, self.update_map)
                else:
                    consecutive_failures += 1
                
                # Update status based on failures
                if consecutive_failures > 10:
                    self.root.after(0, lambda: self.gps_status_label.config(
                        text="🔴 No GPS Data", foreground='red'))
                elif consecutive_failures > 3:
                    self.root.after(0, lambda: self.gps_status_label.config(
                        text="🟡 GPS Signal Weak", foreground='orange'))
                
            except Exception as e:
                print(f"GPS monitoring error: {e}")
                consecutive_failures += 1
            
            time.sleep(self.gps_check_interval)
    
    def read_gps_coordinates(self):
        """Read GPS coordinates from Flutter-generated file"""
        try:
            if not os.path.exists(self.gps_file):
                return False
            
            with open(self.gps_file, 'r') as f:
                data = json.load(f)
            
            new_lat = data.get('latitude')
            new_lon = data.get('longitude')
            timestamp = data.get('timestamp')
            accuracy = data.get('accuracy')
            
            if new_lat is not None and new_lon is not None:
                # Check if coordinates changed significantly
                lat_diff = abs(self.latitude - new_lat) if self.latitude else 1
                lon_diff = abs(self.longitude - new_lon) if self.longitude else 1
                
                if lat_diff > 0.00001 or lon_diff > 0.00001:  # ~1 meter accuracy
                    self.latitude = float(new_lat)
                    self.longitude = float(new_lon)
                    self.accuracy = accuracy
                    self.last_update = timestamp
                    self.add_to_history(self.latitude, self.longitude)
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error reading GPS file: {e}")
            return False
    
    def auto_check_gps(self):
        """Automatically check for GPS file periodically"""
        if os.path.exists(self.gps_file) and not self.live_gps_enabled:
            self.gps_status_label.config(text="🟢 GPS File Found", foreground='green')
            self.status_var.set("GPS file detected - Enable Live Tracking to start monitoring")
        
        # Schedule next check
        self.root.after(5000, self.auto_check_gps)
    
    def test_server_connection(self):
        """Test connection to Flask server"""
        try:
            response = requests.get("http://localhost:5000/health", timeout=5)
            if response.status_code == 200:
                messagebox.showinfo("Server Test", "✅ Flask server is running and accessible!")
            else:
                messagebox.showwarning("Server Test", f"⚠️ Server responded with status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Server Test", "❌ Cannot connect to Flask server.\n\nMake sure receiver_server.py is running!")
        except Exception as e:
            messagebox.showerror("Server Test", f"❌ Error testing server: {e}")
    
    def check_gps_file(self):
        """Check GPS file status"""
        if os.path.exists(self.gps_file):
            try:
                with open(self.gps_file, 'r') as f:
                    data = json.load(f)
                
                file_size = os.path.getsize(self.gps_file)
                messagebox.showinfo("GPS File Status", 
                                  f"✅ GPS file found!\n\n"
                                  f"File: {self.gps_file}\n"
                                  f"Size: {file_size} bytes\n\n"
                                  f"Latest coordinates:\n"
                                  f"Latitude: {data.get('latitude', 'N/A')}\n"
                                  f"Longitude: {data.get('longitude', 'N/A')}\n"
                                  f"Timestamp: {data.get('timestamp', 'N/A')}")
            except Exception as e:
                messagebox.showerror("GPS File Error", f"❌ Error reading GPS file: {e}")
        else:
            messagebox.showwarning("GPS File Status", 
                                 f"⚠️ GPS file not found!\n\n"
                                 f"Expected: {self.gps_file}\n\n"
                                 f"Make sure:\n"
                                 f"1. Flask server is running\n"
                                 f"2. Flutter app is sending GPS data\n"
                                 f"3. Network connection is working")
    
    def update_gps_display(self):
        """Update GPS information in UI"""
        self.gps_status_label.config(text="🟢 GPS Active", foreground='green')
        self.coords_info_label.config(text=f"Coordinates: {self.latitude:.6f}, {self.longitude:.6f}")
        
        if self.accuracy:
            self.accuracy_label.config(text=f"Accuracy: ±{self.accuracy}m")
        else:
            self.accuracy_label.config(text="Accuracy: Not provided")
        
        if self.last_update:
            try:
                # Handle Flutter timestamp format
                timestamp = self.last_update.replace('Z', '+00:00')
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M:%S")
                self.last_update_label.config(text=f"Last Update: {time_str}")
            except:
                self.last_update_label.config(text=f"Last Update: {self.last_update}")
        
        self.location_name = "Live Flutter GPS"
        self.location_info_label.config(text=self.location_name)
    
    def add_to_history(self, lat, lon):
        """Add location to tracking history"""
        self.location_history.append((lat, lon, time.time()))
        if len(self.location_history) > self.max_history:
            self.location_history.pop(0)
    
    def clear_history(self):
        """Clear location history"""
        self.location_history.clear()
        self.update_map()
        self.status_var.set("Location history cleared")
    
    def get_static_map_url(self):
        """Generate Google Static Maps API URL"""
        base_url = "https://maps.googleapis.com/maps/api/staticmap"
        
        params = {
            'center': f"{self.latitude},{self.longitude}",
            'zoom': self.zoom_var.get(),
            'size': self.map_size,
            'scale': self.scale,
            'maptype': self.map_type_var.get(),
            'key': self.api_key
        }
        
        # Current location marker (red)
        markers = f"color:red|label:📱|{self.latitude},{self.longitude}"
        
        # Add path from history
        if len(self.location_history) > 1:
            path_coords = [f"{lat},{lon}" for lat, lon, _ in self.location_history]
            if path_coords:
                params['path'] = "color:blue|weight:3|" + "|".join(path_coords)
        
        params['markers'] = markers
        
        # Build URL
        url = base_url + "?" + "&".join([f"{key}={value}" for key, value in params.items()])
        return url
    
    def download_map_image(self):
        """Download map from Google Static Maps API"""
        try:
            url = self.get_static_map_url()
            self.status_var.set("Downloading map...")
            
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            if 'image' not in response.headers.get('content-type', ''):
                error_text = response.text
                if 'API key' in error_text:
                    raise Exception("Invalid Google Maps API key!")
                elif 'quota' in error_text.lower():
                    raise Exception("API quota exceeded!")
                else:
                    raise Exception(f"API Error: {error_text}")
            
            # Process image
            image = Image.open(BytesIO(response.content))
            
            # Scale for display
            canvas_width = max(self.canvas.winfo_width(), 800)
            canvas_height = max(self.canvas.winfo_height(), 600)
            orig_width, orig_height = image.size
            
            scale_factor = min(canvas_width / orig_width, canvas_height / orig_height)
            if scale_factor > 1:
                new_width = int(orig_width * scale_factor)
                new_height = int(orig_height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            return ImageTk.PhotoImage(image), image.size
            
        except Exception as e:
            raise Exception(f"Map download failed: {str(e)}")
    
    def update_map_thread(self):
        """Update map in background thread"""
        try:
            photo, size = self.download_map_image()
            self.root.after(0, self.display_map, photo, size)
        except Exception as e:
            self.root.after(0, self.show_error, str(e))
    
    def display_map(self, photo, size):
        """Display map on canvas"""
        try:
            self.canvas.delete("all")
            
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                x = (canvas_width - size[0]) // 2
                y = (canvas_height - size[1]) // 2
            else:
                x, y = 0, 0
            
            self.canvas.create_image(max(0, x), max(0, y), anchor=tk.NW, image=photo)
            self.canvas.image = photo
            
            timestamp = time.strftime("%H:%M:%S")
            accuracy_info = f" (±{self.accuracy}m)" if self.accuracy else ""
            self.status_var.set(f"Map updated at {timestamp} - GPS: {self.latitude:.6f}, {self.longitude:.6f}{accuracy_info}")
            
        except Exception as e:
            self.show_error(f"Display error: {str(e)}")
    
    def show_error(self, error_msg):
        """Show error on canvas"""
        self.canvas.delete("all")
        canvas_width = max(self.canvas.winfo_width(), 400)
        canvas_height = max(self.canvas.winfo_height(), 300)
        
        self.canvas.create_text(canvas_width//2, canvas_height//2,
                               text=f"❌ {error_msg}", 
                               fill="red", font=('Arial', 12, 'bold'), 
                               width=min(600, canvas_width-50), justify=tk.CENTER)
        self.status_var.set(f"Error: {error_msg}")
    
    def update_map(self):
        """Update map display"""
        if not self.api_key or self.api_key == "YOUR_GOOGLE_MAPS_API_KEY_HERE":
            self.show_error("Please set your Google Maps API key in the code")
            return
        
        threading.Thread(target=self.update_map_thread, daemon=True).start()
    
    def on_closing(self):
        """Handle window closing"""
        self.live_gps_enabled = False
        if self.gps_thread and self.gps_thread.is_alive():
            self.gps_thread.join(timeout=2)
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        print("🛰️ Live GPS Maps Viewer - Flutter Compatible")
        print(f"📂 GPS data file: {self.gps_file}")
        print("📱 Compatible with Flutter GPS apps")
        print("🔗 Make sure Flask server is running on port 5000")
        print("=" * 60)
        self.root.mainloop()

if __name__ == "__main__":
    app = LiveGPSMapsViewer()
    app.run()