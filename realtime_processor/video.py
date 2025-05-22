import cv2
import os
import glob

def create_video(image_folder, output_path, fps=0.5):
    images = sorted(glob.glob(os.path.join(image_folder, "*.png")))
    print(images)
    if not images:
        print("No PNG images found in", image_folder)
        return

    # Read the first image to get the size
    frame = cv2.imread(images[0])
    height, width, layers = frame.shape
    print(f"Image size: {width}x{height}")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for image in images:
        print(f"Processing image: {image}")
        frame = cv2.imread(image)
        video.write(frame)

    video.release()
    print(f"Video saved to {output_path}")