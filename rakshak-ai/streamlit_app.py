"""
Rakshak AI - Streamlit Web Application
======================================
Car Accident Detection System using YOLO

This is the Streamlit version of the Rakshak AI app, designed for easy
deployment on Streamlit Cloud.

Features:
- Image upload for vehicle detection
- Video upload for accident analysis
- Real-time detection results
- Accident statistics dashboard
- Easy deployment to Streamlit Cloud

Usage:
    streamlit run streamlit_app.py
"""

import streamlit as st
import cv2
import numpy as np
import os
import tempfile
from datetime import datetime
import pandas as pd

# Import the model logic
from model_logic import (
    load_model,
    detect_vehicles,
    check_accident,
    analyze_video_frame,
    is_demo_mode,
    get_vehicle_classes
)

# Page configuration
st.set_page_config(
    page_title="Rakshak AI - Car Accident Detection",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
DEMO_MODE_WARNING = """
⚠️ **Demo Mode Active**: The YOLO model is not loaded. This may be because:
1. The model file (models/yolov8n.pt) is not present
2. The required dependencies are not installed

To enable full functionality, ensure the model file exists and dependencies are installed.
"""

def initialize_model():
    """Initialize the YOLO model."""
    with st.spinner("Loading YOLO model..."):
        model = load_model()
    return model


def process_uploaded_image(uploaded_file):
    """
    Process an uploaded image file.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        dict: Detection results
    """
    # Convert uploaded file to image
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if image is None:
        return {'error': 'Failed to decode image', 'vehicle_count': 0}
    
    # Detect vehicles
    annotated_image, vehicle_count, boxes = detect_vehicles(image)
    
    # Check for accidents
    accident_detected, severity = check_accident(boxes)
    
    # Convert annotated image to RGB for display
    annotated_rgb = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)
    
    return {
        'annotated_image': annotated_rgb,
        'vehicle_count': vehicle_count,
        'accident_detected': accident_detected,
        'severity': severity,
        'boxes': boxes,
        'demo_mode': is_demo_mode()
    }


def process_uploaded_video(uploaded_file):
    """
    Process an uploaded video file.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        dict: Processing results with video path and stats
    """
    # Save uploaded video to temp file
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    tfile.close()
    
    # Open video capture
    cap = cv2.VideoCapture(tfile.name)
    
    if not cap.isOpened():
        os.unlink(tfile.name)
        return {'error': 'Failed to open video', 'total_frames': 0}
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Process frames
    frame_count = 0
    accident_frames = []
    max_vehicle_count = 0
    
    # Create video writer for output
    output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Analyze frame
        annotated_frame, vehicle_count, accident_flag, severity = analyze_video_frame(frame)
        
        # Update statistics
        frame_count += 1
        max_vehicle_count = max(max_vehicle_count, vehicle_count)
        
        if accident_flag:
            accident_frames.append({
                'frame': frame_count,
                'severity': severity,
                'vehicle_count': vehicle_count
            })
        
        # Write annotated frame
        out.write(annotated_frame)
        
        # Update progress
        progress = frame_count / total_frames
        progress_bar.progress(progress)
        status_text.text(f"Processing frame {frame_count}/{total_frames}")
    
    # Release resources
    cap.release()
    out.release()
    
    # Clean up input temp file
    os.unlink(tfile.name)
    
    return {
        'output_video': output_path,
        'total_frames': frame_count,
        'accident_frames': accident_frames,
        'max_vehicle_count': max_vehicle_count,
        'fps': fps,
        'width': width,
        'height': height,
        'demo_mode': is_demo_mode()
    }


def main():
    """Main Streamlit application."""
    
    # Header
    st.title("🚗 Rakshak AI")
    st.markdown("### Car Accident Detection System")
    st.markdown("---")
    
    # Check demo mode
    if is_demo_mode():
        st.warning(DEMO_MODE_WARNING)
    
    # Sidebar
    st.sidebar.title("⚙️ Configuration")
    
    # Input selection
    input_type = st.sidebar.radio(
        "Select Input Type:",
        ["Image Analysis", "Video Analysis", "Statistics Dashboard"]
    )
    
    # Settings
    st.sidebar.markdown("### Detection Settings")
    overlap_threshold = st.sidebar.slider(
        "Overlap Threshold",
        min_value=0.5,
        max_value=1.0,
        value=0.8,
        step=0.05,
        help="IoU threshold for detecting vehicle collisions"
    )
    
    min_area = st.sidebar.slider(
        "Minimum Intersection Area",
        min_value=1000,
        max_value=10000,
        value=5000,
        step=500,
        help="Minimum intersection area to consider as collision"
    )
    
    # Info section
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ About")
    st.sidebar.info(
        "Rakshak AI uses YOLO (You Only Look Once) computer vision "
        "to detect vehicles and identify potential accidents through "
        "collision detection algorithms."
    )
    
    # Main content based on selection
    if input_type == "Image Analysis":
        image_analysis_section(overlap_threshold, min_area)
    elif input_type == "Video Analysis":
        video_analysis_section(overlap_threshold, min_area)
    else:
        statistics_dashboard_section()


def image_analysis_section(overlap_threshold, min_area):
    """Image analysis section."""
    st.header("📷 Image Analysis")
    st.markdown("Upload an image to detect vehicles and check for potential accidents.")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose an image...",
        type=['jpg', 'jpeg', 'png', 'bmp']
    )
    
    if uploaded_file is not None:
        # Process button
        if st.button("🔍 Analyze Image", type="primary"):
            with st.spinner("Processing image..."):
                results = process_uploaded_image(uploaded_file)
            
            if 'error' in results:
                st.error(f"Error: {results['error']}")
            else:
                # Display results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📸 Original Image")
                    st.image(uploaded_file, use_container_width=True)
                
                with col2:
                    st.subheader("🔍 Detection Result")
                    st.image(results['annotated_image'], use_container_width=True)
                
                # Statistics
                st.markdown("### 📊 Detection Results")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Vehicles Detected", results['vehicle_count'])
                
                with col2:
                    accident_status = "⚠️ YES" if results['accident_detected'] else "✅ No"
                    st.metric("Accident Detected", accident_status)
                
                with col3:
                    severity = results['severity']
                    severity_label = f"Level {severity}/5" if severity > 0 else "N/A"
                    st.metric("Severity", severity_label)
                
                with col4:
                    st.metric("Demo Mode", "Yes" if results['demo_mode'] else "No")
                
                # Alert if accident detected
                if results['accident_detected']:
                    st.error(
                        f"🚨 **ALERT: Potential Accident Detected!**\n\n"
                        f"Severity Level: {results['severity']}/5\n"
                        f"Vehicles Involved: {results['vehicle_count']}"
                    )


def video_analysis_section(overlap_threshold, min_area):
    """Video analysis section."""
    st.header("🎬 Video Analysis")
    st.markdown("Upload a video to analyze vehicle movements and detect potential accidents.")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a video...",
        type=['mp4', 'avi', 'mov', 'mkv']
    )
    
    if uploaded_file is not None:
        # Process button
        if st.button("🎥 Analyze Video", type="primary"):
            with st.spinner("Processing video... This may take a while..."):
                results = process_uploaded_video(uploaded_file)
            
            if 'error' in results:
                st.error(f"Error: {results['error']}")
            else:
                # Display statistics
                st.success(f"Video processed successfully!")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Frames", results['total_frames'])
                
                with col2:
                    st.metric("Max Vehicles", results['max_vehicle_count'])
                
                with col3:
                    accident_count = len(results['accident_frames'])
                    st.metric("Accidents Detected", accident_count)
                
                with col4:
                    st.metric("FPS", results['fps'])
                
                # Show accident frames
                if results['accident_frames']:
                    st.warning(
                        f"🚨 **{len(results['accident_frames'])} Potential Accident(s) Detected!**"
                    )
                    
                    # Create accident timeline
                    accident_df = pd.DataFrame(results['accident_frames'])
                    if not accident_df.empty:
                        st.markdown("### Accident Timeline")
                        st.dataframe(
                            accident_df.rename(columns={
                                'frame': 'Frame #',
                                'severity': 'Severity',
                                'vehicle_count': 'Vehicles'
                            }),
                            use_container_width=True
                        )
                
                # Download button for annotated video
                with open(results['output_video'], 'rb') as f:
                    video_bytes = f.read()
                
                st.download_button(
                    label="📥 Download Annotated Video",
                    data=video_bytes,
                    file_name="rakshak_analysis.mp4",
                    mime="video/mp4"
                )
                
                # Clean up
                os.unlink(results['output_video'])


def statistics_dashboard_section():
    """Statistics dashboard section."""
    st.header("📈 Statistics Dashboard")
    
    # Check for database
    db_path = os.path.join(os.path.dirname(__file__), 'accidents.db')
    
    if not os.path.exists(db_path):
        st.info("No accident database found. The database will be created when accidents are detected.")
        st.markdown("### How Statistics Work")
        st.markdown("""
        The statistics dashboard shows historical accident data from the database.
        When using the Flask app with real-time detection, accidents are logged to
        the database and will appear here.
        
        For now, you can:
        1. Use the **Image Analysis** or **Video Analysis** features
        2. Run the Flask app for real-time monitoring
        3. Accidents detected will be logged to the database
        """)
    else:
        try:
            import sqlite3
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get total accidents
            cursor.execute("SELECT COUNT(*) FROM accidents")
            total_accidents = cursor.fetchone()[0]
            
            # Get recent accidents
            cursor.execute("SELECT * FROM accidents ORDER BY timestamp DESC LIMIT 10")
            recent_accidents = cursor.fetchall()
            
            # Get severity distribution
            cursor.execute("SELECT severity, COUNT(*) FROM accidents GROUP BY severity")
            severity_dist = cursor.fetchall()
            
            conn.close()
            
            # Display statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Accidents", total_accidents)
            
            with col2:
                if severity_dist:
                    avg_severity = sum(s * c for s, c in severity_dist) / total_accidents if total_accidents > 0 else 0
                    st.metric("Average Severity", f"{avg_severity:.1f}/5")
                else:
                    st.metric("Average Severity", "N/A")
            
            with col3:
                st.metric("Data Points", total_accidents)
            
            # Severity distribution chart
            if severity_dist:
                st.markdown("### Severity Distribution")
                severity_df = pd.DataFrame(severity_dist, columns=['Severity', 'Count'])
                st.bar_chart(severity_df.set_index('Severity'))
            
            # Recent accidents table
            if recent_accidents:
                st.markdown("### Recent Accidents")
                accidents_df = pd.DataFrame(
                    recent_accidents,
                    columns=['ID', 'Timestamp', 'Latitude', 'Longitude', 'Severity', 'Description']
                )
                st.dataframe(
                    accidents_df.drop(columns=['ID', 'Latitude', 'Longitude']),
                    use_container_width=True
                )
            else:
                st.info("No accidents recorded yet.")
        
        except Exception as e:
            st.error(f"Error reading database: {e}")


if __name__ == "__main__":
    main()
