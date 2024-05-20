import os

import cv2
import numpy as np


def is_black_frame(frame, threshold=0.01):
    """Check if the frame is black."""
    return np.sum(frame) <= threshold * np.prod(frame.shape)


def save_clip(frames, output_filename, fps=15.0):
    """Save frames as a new video file."""
    # Ensure the output directory exists
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Include the output directory in the filename
    output_filename = os.path.join(output_dir, output_filename)

    height, width, _ = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_filename, fourcc, fps, (width, height))

    for frame in frames:
        out.write(frame)

    out.release()


def split_on_black_frames(video_filename, output_fps=15.0):
    """Split video into multiple clips at black frames."""
    cap = cv2.VideoCapture(video_filename)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    input_fps = cap.get(cv2.CAP_PROP_FPS)  # Get the fps of the original video
    frame_skip = round(input_fps / output_fps)  # Calculate how many frames to skip
    clip_num = 0
    frames = []

    while(cap.isOpened()):
        ret, frame = cap.read()
        current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

        if not ret:
            break

        if is_black_frame(frame):
            if frames:
                save_clip(frames, f'clip_{clip_num}.mp4', output_fps)
                frames = []
                clip_num += 1
        elif current_frame % frame_skip == 0:  # Only append every nth frame
            frames.append(frame)

        # Print progress
        progress = (current_frame / total_frames) * 100
        print(f'Progress: {progress:.2f}%')

    # Save the last clip if it's not empty
    if frames:
        save_clip(frames, f'clip_{clip_num}.mp4', output_fps)

    cap.release()


# Use the function
split_on_black_frames('test2.mp4', output_fps=15.0)
