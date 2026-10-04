import cv2
from pathlib import Path
from moviepy import VideoFileClip
import numpy as np
import requests

def original_filter(edited_frame, array, changed):
    array[changed] += 1
    # We can use NumPy's advanced indexing to apply the color mapping in a more efficient way
    # When we do array > or < NumPy applies the condition to each element, returns the array that meets the condition, and we can use that to index into the edited_frame array and set the color values.
    edited_frame[(array >= 50) & (array < 100)] = [255, 0, 0]
    edited_frame[(array >= 100) & (array < 150)] = [128, 0, 128]
    edited_frame[(array >= 150) & (array < 200)] = [0, 0, 255]
    edited_frame[(array >= 200) & (array < 250)] = [0, 165, 255]
    edited_frame[(array >= 250) & (array < 300)] = [0, 255, 255]
    edited_frame[array >= 300] = [255, 255, 255]

def new_filter(edited_frame, array, changed):
    array[changed] += 1
    changed_array = array.astype(np.uint32)

    # Modulo 180 wraps the values back to the start since they go from 0-179 (in OpenCV)
    hue = (changed_array % 180).astype(np.uint8)
    saturation = np.full_like(hue, 255, dtype=np.uint8)
    value = np.full_like(hue, 255, dtype=np.uint8)
    hsv = cv2.merge([hue, saturation, value])

    cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB, dst=edited_frame)

def create_directory(name: str):
    # Create the directory if it doesn't exist
    filepath = Path(__file__).parent / name
    if not filepath.exists():
        filepath.mkdir(parents=True, exist_ok=True)

    return filepath

def download_video(url: str, output_filename: str):
    print(f"Downloading video from {url}...")
    with requests.get(url, stream=True) as response:
        response.raise_for_status()

        with open(output_filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    print(f"Video downloaded and saved as {output_filename}.")


def generate_video(input_video_name: str, output_video_name: str):
    # Create the video directory if it doesn't exist
    filepath = create_directory("video")
    videopath = filepath / input_video_name

    if not videopath.exists():
        download_video("https://badapple.mov/badapple.mov", str(videopath))
        

    cap = cv2.VideoCapture(str(videopath))

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    # Create the output directory if it doesn't exist
    output_path = create_directory("output")
    out = cv2.VideoWriter(str(output_path / str(output_video_name + ".mp4")), fourcc, fps, (width, height))

    array = np.zeros((height, width), dtype=np.uint16)

    past_frame = None
    frame_count = 0;

    while cap.isOpened():
        print(f"Processing frame {frame_count}/{total_frame}")

        ret, frame = cap.read()
        if not ret:
            break

        # Convert the frame to grayscale and then to a two-color image using Otsu's thresholding
        # We do this becuase when we don't there couble minor color changes due to video compression
        gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresholded_2d = cv2.threshold(gray_image, 0, 255, cv2.THRESH_OTSU)

        # We need to convert the 2D image back into a 3D image to compare both frames
        two_color_image = cv2.cvtColor(thresholded_2d, cv2.COLOR_GRAY2BGR)

        edited_frame = two_color_image.copy()
        if past_frame is not None:
            changed = np.any(two_color_image != past_frame, axis=2)
            new_filter(edited_frame, array, changed)


        past_frame = two_color_image.copy()
        frame_count += 1

        out.write(edited_frame)
        cv2.imshow('Bad Apple', edited_frame)

        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()


    # Add audio to the video
    audio_clip = VideoFileClip(videopath).audio
    output_clip = VideoFileClip(output_path / str(output_video_name + ".mp4"))

    final_clip = output_clip.with_audio(audio_clip)
    final_clip.write_videofile(str(output_path / str(output_video_name + "_sound.mp4")), codec="libx264", audio_codec="aac", audio=True )

    audio_clip.close()
    output_clip.close()
    final_clip.close()

def main():
    input_video_name = "bad_apple.mov"
    output_video_name = "bad_apple_output"
    generate_video(input_video_name, output_video_name)


if __name__ == "__main__":
    main()
