# Video Clipper

## Installation

Required: python > 3.10

Install with poetry:

```bash
poetry install
```

Enter the shell:

```bash
poetry shell
```

## Usage

Copy the example.env file to .env and add your name.

Then:

```bash
cd video-dataset-tools
```

Run streamlit app:

```bash
streamlit run main.py
```

## Process

1. Record your videos
2. Put your videos in the `video_to_process` folder
3. Run the app
4. Once finished processing the videos click on the archive button
5. Delete the videos from the `video_to_process` folder
6. Terminate the streamlit app

Now you need to send the processed videos to who is merging them.

To do that:

1. Zip the `{name}_processed_videos` folder
2. Send the zip file to the person who is merging the videos

The person who is merging the videos will:

1. Unzip the file in the `video_to_merge` folder

