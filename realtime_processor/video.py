import cv2
import glob
import os
import sys

def main():
    if len(sys.argv) != 4:
        print("Usage: python video.py <image_folder> <frequency> <fps>")
        sys.exit(1)

    image_folder = sys.argv[1]
    frequency = sys.argv[2]
    try:
        fps = float(sys.argv[3])
    except ValueError:
        print("FPS must be a number")
        sys.exit(1)

    # Find images matching the frequency
    pattern = f"*sky_calibrated_{frequency}*.png"
    image_files = sorted(glob.glob(os.path.join(image_folder, pattern)))
    print(f"Found {len(image_files)} images matching pattern '{pattern}' in '{image_folder}'")
    if not image_files:
        print("No images found")
        sys.exit(1)

    first = cv2.imread(image_files[0])
    h, w = first.shape[:2]
    output_file = os.path.join(image_folder, f"movie_for_sky_calibrated_{frequency}.mp4")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(output_file, fourcc, fps, (w, h))

    for filename in image_files:
        img = cv2.imread(filename)
        if img is None:
            continue

        if img.shape[0] != h or img.shape[1] != w:
            img = cv2.resize(img, (w, h))
        video.write(img)

    video.release()
    print(f"Video saved as {output_file}")

if __name__ == "__main__":
    main()
