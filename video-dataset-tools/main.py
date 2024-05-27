from datetime import datetime
import multiprocessing
import shutil

import cv2
import streamlit as st
import os

from PIL import Image
from moviepy.editor import VideoFileClip
import numpy as np
from streamlit_drawable_canvas import st_canvas
from loguru import logger
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Get the author variable
author = os.getenv('AUTHOR')
author = author.lower() if author is not None else None

input_video_folder = "video_to_process"
output_video_folder = f"{author}_processed_videos"
skipped_folder = "skipped"
target_fps = 15


def increment_video_index(video_files):
    st.session_state.video_id += 1
    st.session_state.video_index = (st.session_state.video_index + 1) % video_files


def decrement_video_index():
    st.session_state.video_id = max(0, st.session_state.video_id - 1)
    st.session_state.video_index = max(0, st.session_state.video_index - 1)


def handle_save_video(main_col, col, video_path, start_time, end_time, video_files, boxes):
    col1, col2 = main_col.columns(2)

    prefix = col2.text_input('Prefix', value=author)

    action = col1.radio('Select action', ['fall', 'slow_fall', 'sit', 'walk', 'lay'])
    save_with_mask = col2.checkbox('Save with mask')

    if col.button('Save Video ✅', type='primary'):
        process = multiprocessing.Process(target=process_video, args=(
            video_path, start_time, end_time, action, save_with_mask, boxes, prefix))
        process.start()

        increment_video_index(len(video_files))
        st.experimental_rerun()


def handle_skip_video(col, video_path, video_files):
    if col.button('Skip Video ❌'):
        os.makedirs(skipped_folder, exist_ok=True)
        shutil.copy(video_path, os.path.join(skipped_folder, f"{st.session_state.video_id}.mp4"))

        increment_video_index(len(video_files))
        st.experimental_rerun()


def handle_previous_video(col):
    if col.button('⏪ Previous Video'):
        decrement_video_index()
        st.experimental_rerun()


def handle_next_video(col, number_of_video_files):
    if col.button('Next Video ⏩'):
        increment_video_index(number_of_video_files)
        st.experimental_rerun()


def archive_videos():
    # Get the current date and time
    now = datetime.now()

    # Format the date and time into a string
    datetime_str = now.strftime("%Y-%m-%d_%H-%M")

    # Create the archive/{datetime} directory
    archive_dir = os.path.join("archive", datetime_str)
    os.makedirs(archive_dir, exist_ok=True)

    # Get a list of all files in the video_to_process directory
    video_files = os.listdir(input_video_folder)

    # For each file in the video_to_process directory
    for idx, video_file in enumerate(video_files):
        logger.info(f"Archiving {video_file} ({idx + 1}/{len(video_files)})")
        # Construct the full file paths
        src_file = os.path.join(input_video_folder, video_file)
        dst_file = os.path.join(archive_dir, video_file)

        # Copy the file to the archive/{datetime} directory
        shutil.copy2(src_file, dst_file)

    logger.success("All videos have been archived.")


def display_video_info(target_duration, number_of_video_files, video_path, start_time, end_time, video_files, boxes):
    main_col = st.sidebar.container()

    # If all the video files have been processed, show balloons
    if st.session_state.video_id == number_of_video_files:
        st.balloons()

        if st.sidebar.button("Archive Videos"):
            logger.warning("Archiving videos. Do not close the browser or refresh the page.")
            process = multiprocessing.Process(target=archive_videos)
            process.start()

    main_col.title("Target Video Information")
    col1, col2 = main_col.columns(2)
    col1.metric(label="Framerate", value=f"{target_fps} fps")
    col2.metric(label="Length", value=f"{target_duration} sec")

    col1, col2 = st.sidebar.columns(2)

    handle_save_video(main_col, col1, video_path, start_time, end_time, video_files, boxes)
    handle_skip_video(col2, video_path, video_files)
    main_col.progress(st.session_state.video_id / number_of_video_files)
    main_col.write(f"{st.session_state.video_id}/{number_of_video_files} video processed")

    handle_previous_video(col1)
    handle_next_video(col2, number_of_video_files)


def process_video(video_path, start_time, end_time, action, save_with_mask, boxes, prefix):
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

    # Get the number of files in the subdirectory
    files = os.listdir(output_folder)
    video_id = len(files)

    # Generate the filename based on the prefix and video id
    filename = f"{prefix}_{action}_{video_id}.mp4" if prefix else f"{action}_{video_id}.mp4"

    # Write the clipped video to the output folder with a progressive id
    output_path = os.path.join(output_folder, filename)

    # Check if the file already exists
    if os.path.exists(output_path):
        st.error(f"Video {output_path} already exists. Not overwriting.")
        logger.error(f"Video {output_path} already exists. Not overwriting.")
        return

    subclip.without_audio().write_videofile(output_path, fps=target_fps)

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

    return bboxes


def main():
    # List all files in the directory
    files = os.listdir(input_video_folder)

    # Filter out the video files
    video_files = [file for file in files if file.endswith(('.mp4', '.avi'))]

    # Create a session state for the video index and video id
    if 'video_index' not in st.session_state:
        st.session_state.video_index = 0
    if 'video_id' not in st.session_state:
        st.session_state.video_id = 0

    # Get the current video file
    video_file = video_files[st.session_state.video_index]
    video_path = os.path.join(input_video_folder, video_file)

    # Display the name of the video
    st.markdown(f"### Video: {video_file}")

    # Get the duration of the video
    clip = VideoFileClip(video_path)
    video_duration = int(clip.duration)

    # Add a range slider underneath the video
    range_slider = st.slider('Select a range', 0, video_duration, (0, video_duration))

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
    if author is None or author == '':
        st.error('Author is not defined. Please define the author variable in .env file.')
    else:
        main()
