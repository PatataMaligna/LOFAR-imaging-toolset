import cv2
import os
import glob

def create_video(image_folder, output_path, fps=2):
    images = sorted(glob.glob(os.path.join(image_folder, "*.png")))
    if not images:
        print("No PNG images found in", image_folder)
        return

    # Read the first image to get the size
    frame = cv2.imread(images[0])
    height, width, layers = frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for image in images:
        frame = cv2.imread(image)
        video.write(frame)

    video.release()
    print(f"Video saved to {output_path}")