import multiprocessing
import shutil

import cv2
import streamlit as st
import os
from moviepy.editor import VideoFileClip
import numpy as np

input_video_folder = "raw_videos"
output_video_folder = "output_videos"
skipped_folder = "skipped"
target_fps = 15


def display_video_info(target_duration, number_of_video_files, video_path, start_time, end_time, video_files,
                       top_x, top_y, bottom_x, bottom_y):
    # If all the video files have been processed, show balloons
    if st.session_state.video_id == number_of_video_files:
        st.balloons()

    # Display video information in the sidebar
    # st.sidebar.title("Source Video Information")
    # st.sidebar.write(f"Resolution: {clip.size[0]}x{clip.size[1]}")
    # st.sidebar.write(f"Framerate: {clip.fps}")
    # st.sidebar.write(f"Length: {clip.duration}")

    st.sidebar.title("Target Video Information")
    st.sidebar.write(f"Framerate: {target_fps}")
    st.sidebar.metric(label="Length", value=f"{target_duration} sec")

    prefix = st.sidebar.text_input('Prefix', value='')

    # Add a radio button in the sidebar for action selection
    action = st.sidebar.radio('Select action', ['fall', 'slow_fall', 'sit', 'walk', 'lay'])

    # Add a toggle in the sidebar to save the video with the mask
    save_with_mask = st.sidebar.checkbox('Save with mask')

    # Create two columns for the buttons
    col1, col2 = st.sidebar.columns(2)

    # Create a button to save the video
    if col1.button('Save Video ✅', type='primary'):
        # Process the current video in a separate process
        process = multiprocessing.Process(target=process_video, args=(
            video_path, start_time, end_time, st.session_state.video_id, action, save_with_mask,
            ((top_x, top_y), (bottom_x, bottom_y)), prefix))
        process.start()

        st.session_state.video_id += 1
        st.session_state.video_index = (st.session_state.video_index + 1) % len(video_files)
        st.experimental_rerun()

    # Add a button to skip the video
    if col2.button('Skip Video ⏩'):
        # Save the current video to a separate folder without clipping it
        os.makedirs(skipped_folder, exist_ok=True)
        shutil.copy(video_path, os.path.join(skipped_folder, f"{st.session_state.video_id}.mp4"))

        st.session_state.video_id += 1
        st.session_state.video_index = (st.session_state.video_index + 1) % len(video_files)
        st.experimental_rerun()

    # Add a progress bar in the sidebar representing the number of processed videos
    st.sidebar.progress(st.session_state.video_id / number_of_video_files)
    st.sidebar.write(f"{st.session_state.video_id}/{number_of_video_files} video processed")


def process_video(video_path, start_time, end_time, video_id, action, save_with_mask, rectangle_coordinates, prefix):
    # Load the video
    clip = VideoFileClip(video_path)

    # Clip the video based on the start and end time
    subclip = clip.subclip(start_time, end_time)

    # If the toggle is checked, apply the mask to the video
    if save_with_mask:
        # Create a mask of the same size as the video frames
        mask = np.ones((clip.size[1], clip.size[0]), dtype=np.uint8) * 255

        # Set the pixels inside the rectangle to black
        top_left, bottom_right = rectangle_coordinates
        mask[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]] = 0

        # Apply the mask to each frame of the video
        subclip = subclip.fl_image(lambda image: cv2.bitwise_and(image, image, mask=mask))

    # Create the output folder if it doesn't exist
    output_folder = os.path.join(output_video_folder, f"{target_fps}fps", action)
    os.makedirs(output_folder, exist_ok=True)

    # Generate the filename based on the prefix and video id
    filename = f"{prefix}_{video_id}.mp4" if prefix else f"{video_id}.mp4"

    # Write the clipped video to the output folder with a progressive id
    output_path = os.path.join(output_folder, filename)
    subclip.write_videofile(output_path, fps=target_fps)

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
    # st.write(f"Length (s): {range_slider[1] - range_slider[0]}")

    # Clip the video based on the value of the slider
    start_time, end_time = range_slider

    # Display the clipped video with autoplay
    st.video(video_path, start_time=start_time, end_time=end_time, format="video/mp4", autoplay=True, loop=True,
             muted=True)

    # Get the first frame of the video
    first_frame = clip.get_frame(0)  # 0 indicates the start of the video

    # Convert the frame to RGB format
    first_frame_rgb = cv2.cvtColor(first_frame, cv2.COLOR_BGR2RGB)

    # Add sliders to specify the top-left and bottom-right coordinates of the rectangle
    top_x, bottom_x = st.slider('Top-left coordinate (x, y)', 0, clip.size[0], (0, 0))
    top_y, bottom_y = st.slider('Bottom-right coordinate (x, y)', 0, clip.size[1], (0, 0))

    # Draw a rectangle on the first frame
    cv2.rectangle(first_frame_rgb, (top_x, top_y), (bottom_x, bottom_y), (255, 0, 0),
                  2)  # The rectangle is drawn in red color

    # Display the first frame with the rectangle
    st.image(first_frame_rgb[..., ::-1], caption='First frame of the video', use_column_width=True)
    clip.close()

    display_video_info(range_slider[1] - range_slider[0], len(video_files), video_path, start_time, end_time,
                       video_files, top_x, top_y, bottom_x, bottom_y)


if __name__ == "__main__":
    st.title("Video Dataset Tools")
    main()
