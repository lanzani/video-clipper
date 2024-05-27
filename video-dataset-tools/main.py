import multiprocessing
import shutil

import cv2
import streamlit as st
import os

from PIL import Image
from moviepy.editor import VideoFileClip
import numpy as np
from streamlit_drawable_canvas import st_canvas
import pandas as pd

input_video_folder = "raw_videos"
output_video_folder = "output_videos"
skipped_folder = "skipped"
target_fps = 15


def display_video_info(target_duration, number_of_video_files, video_path, start_time, end_time, video_files, boxes):
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
    save_with_mask = st.sidebar.toggle('Save with mask')

    # Create two columns for the buttons
    col1, col2 = st.sidebar.columns(2)

    # Create a button to save the video
    if col1.button('Save Video ✅', type='primary'):
        # Process the current video in a separate process
        process = multiprocessing.Process(target=process_video, args=(
            video_path, start_time, end_time, st.session_state.video_id, action, save_with_mask, boxes, prefix))
        process.start()

        st.session_state.video_id += 1
        st.session_state.video_index = (st.session_state.video_index + 1) % len(video_files)
        st.experimental_rerun()

    # Add a button to skip the video
    if col2.button('Skip Video ❌'):
        # Save the current video to a separate folder without clipping it
        os.makedirs(skipped_folder, exist_ok=True)
        shutil.copy(video_path, os.path.join(skipped_folder, f"{st.session_state.video_id}.mp4"))

        st.session_state.video_id += 1
        st.session_state.video_index = (st.session_state.video_index + 1) % len(video_files)
        st.experimental_rerun()

    # Add a progress bar in the sidebar representing the number of processed videos
    st.sidebar.progress(st.session_state.video_id / number_of_video_files)
    st.sidebar.write(f"{st.session_state.video_id}/{number_of_video_files} video processed")

    # Create two columns for the navigation buttons
    col1, col2 = st.sidebar.columns(2)

    # Add a button to go to the previous video
    if col1.button('⏪ Previous Video'):
        st.session_state.video_id = max(0, st.session_state.video_id - 1)
        st.session_state.video_index = max(0, st.session_state.video_index - 1)
        st.experimental_rerun()

    # Add a button to go to the next video
    if col2.button('Next Video ⏩'):
        st.session_state.video_id = min(number_of_video_files - 1, st.session_state.video_id + 1)
        st.session_state.video_index = min(len(video_files) - 1, st.session_state.video_index + 1)
        st.experimental_rerun()


def process_video(video_path, start_time, end_time, video_id, action, save_with_mask, boxes, prefix):
    # Load the video
    clip = VideoFileClip(video_path)

    # Clip the video based on the start and end time
    subclip = clip.subclip(start_time, end_time)

    # If the toggle is checked, apply the mask to the video
    if save_with_mask:
        # Create a mask of the same size as the video frames
        mask = np.ones((clip.size[1], clip.size[0]), dtype=np.uint8) * 255

        for box in boxes:
            # Set the pixels inside the rectangle to black
            top_left_x, top_left_y, bottom_right_x, bottom_right_y = box
            mask[top_left_y:bottom_right_y, top_left_x:bottom_right_x] = 0

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


def draw_masks(first_frame, width, height):
    # Create a canvas component
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        stroke_width=2,
        stroke_color="000",
        background_image=Image.fromarray(first_frame),
        update_streamlit=True,
        drawing_mode="rect",
        point_display_radius=0,
        key="canvas",
    )

    bboxes = []
    if canvas_result.json_data is not None:
        for rect in canvas_result.json_data["objects"]:
            if rect["type"] == "rect":
                top_x, top_y = rect["left"], rect["top"]
                bottom_x, bottom_y = rect["left"] + rect["width"], rect["top"] + rect["height"]

                # Adapt points to the original image size
                top_x = int(top_x * width / 600)
                top_y = int(top_y * height / 400)
                bottom_x = int(bottom_x * width / 600)
                bottom_y = int(bottom_y * height / 400)

                bboxes.append((top_x, top_y, bottom_x, bottom_y))

    # objects = pd.json_normalize(canvas_result.json_data["objects"])  # need to convert obj to str because PyArrow
    # for col in objects.select_dtypes(include=['object']).columns:
    #     objects[col] = objects[col].astype("str")
    # st.dataframe(objects)

    # # Convert the frame to RGB format
    # first_frame_rgb = cv2.cvtColor(first_frame, cv2.COLOR_BGR2RGB)
    #
    # # Add sliders to specify the top-left and bottom-right coordinates of the rectangle
    # top_x, bottom_x = st.slider('Top-left coordinate (x, y)', 0, width, (0, 0))
    # top_y, bottom_y = st.slider('Bottom-right coordinate (x, y)', 0, height, (0, 0))
    #
    # # Draw a rectangle on the first frame
    # cv2.rectangle(first_frame_rgb, (top_x, top_y), (bottom_x, bottom_y), (255, 0, 0),
    #               2)  # The rectangle is drawn in red color
    #
    # # Display the first frame with the rectangle
    # st.image(first_frame_rgb[..., ::-1], caption='First frame of the video', use_column_width=True)

    return bboxes


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
    clip.close()

    boxes = draw_masks(first_frame, clip.size[0], clip.size[1])

    display_video_info(range_slider[1] - range_slider[0], len(video_files), video_path, start_time, end_time,
                       video_files, boxes)


if __name__ == "__main__":
    st.title("Video Dataset Tools")
    main()
