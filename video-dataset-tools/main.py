import streamlit as st
import os
from moviepy.editor import VideoFileClip

input_video_folder = "input_videos"
output_video_folder = "output_videos"


def process_video(video_path, start_time, end_time, video_id):
    # Load the video
    clip = VideoFileClip(video_path)

    # Clip the video based on the start and end time
    subclip = clip.subclip(start_time, end_time)

    # Write the clipped video to the output folder with a progressive id
    output_path = os.path.join(output_video_folder, f"{video_id}.mp4")
    subclip.write_videofile(output_path, fps=15)

    # Close the video clips to free up memory
    subclip.close()
    clip.close()


def main():
    # List all files in the directory
    files = os.listdir(input_video_folder)

    # Filter out the video files
    video_files = [file for file in files if file.endswith(('.mp4', '.flv', '.avi'))]

    # Create a session state for the video index and video id
    if 'video_index' not in st.session_state:
        st.session_state.video_index = 0
    if 'video_id' not in st.session_state:
        st.session_state.video_id = 0

    # Get the current video file
    video_file = video_files[st.session_state.video_index]
    video_path = os.path.join(input_video_folder, video_file)

    # Get the duration of the video
    clip = VideoFileClip(video_path)
    video_duration = int(clip.duration)

    # Add a range slider underneath the video
    range_slider = st.slider('Select a range', 0, video_duration, (0, video_duration))

    # Display the length of the range slider
    st.write(f"Length of range slider: {range_slider[1] - range_slider[0]}")

    # Clip the video based on the value of the slider
    start_time, end_time = range_slider

    # Display the clipped video with autoplay
    st.video(video_path, start_time=start_time, end_time=end_time, format="video/mp4")

    # Create a button to save the video
    if st.button('Save Video'):
        # Process the current video
        process_video(video_path, start_time, end_time, st.session_state.video_id)
        st.session_state.video_id += 1

    # Create a button to go to the next video
    if st.button('Next Video'):
        st.session_state.video_index = (st.session_state.video_index + 1) % len(video_files)
        st.experimental_rerun()


if __name__ == "__main__":
    st.title("Video Dataset Tools")
    main()