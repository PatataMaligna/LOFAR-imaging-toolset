# 🌌 LOFAR Imaging Toolset

> A real-time data processing tool for **LOFAR** single-station observations

---

## ⚙️ Installation and Execution

### 🐧 Linux

1. **Clone repository**

   ```bash
   git clone https://github.com/PatataMaligna/LOFAR-imaging-toolset.git
   cd LOFAR-imaging-toolset
   ```

2. **Setup Python venv**

   ```bash
   python3.12 -m venv envLofar
   source envLofar/bin/activate
   ```


3. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run processor**

   > **Note:**  
   > You must run the command from the `lofarimaging` folder (the parent of `realtime_processor`), **not** from inside the `realtime_processor` directory.

   ```bash
   taskset -c 0-1 python3.12 -m realtime_processor.main /path/to/your/data
   ```
5. **Install essential system libraries**

   > If you see an error like:  
   > `ImportError: "library" cannot open shared object file: No such file or directory`  
   > it means your system is missing some required libraries.  
   >  
   > The most common ones are:  
   > `libegl1`, `libxkbcommon0`, `libxkbcommon-x11-0`, `libxcb-cursor0`, `libxcb-shape0`  
   >  
   > You can install them all at once with:

   ```bash
   sudo apt update
   sudo apt install libegl1 libxkbcommon0 libxkbcommon-x11-0 libxcb-cursor0 libxcb-shape0
   ```

### 🪟 Windows

1. **Clone repository**

   ```powershell
   git clone https://github.com/PatataMaligna/LOFAR-imaging-toolset.git
   cd LOFAR-imaging-toolset
   ```

2. **Setup Python venv**

   ```powershell
   python -m venv envLofar
   envLofar\Scripts\activate
   ```

3. **Install Python dependencies**

   ```powershell
   pip install -r requirements.txt
   ```

4. **Run processor**

   > **Note:**  
   > Make sure to run the command from the `lofarimaging` folder.

   ```powershell
   python -m realtime_processor.main C:\path\to\your\data
   ```

---

### 📝 How to Use the Software

A sample `.dat` file is provided, along with a `.sh` script inside the data folder, that demonstrates usage with a specific subband (167), which corresponds to a frequency of 32.6 MHz.

#### Enabling Real-Time Processing Mode

To activate real-time processing, append the `--realtime` flag to your execution command. For example:

```bash
taskset -c 0-1 python3.12 -m realtime_processor.main /path/to/your/data --realtime
```

This option enables the tool to process incoming data streams in real time as they are received. Only use if access to LOFAR LV614 is granted.
#### Selecting and Exploring Frequencies

- **Choose a Frequency:**  
   Enter your desired frequency (e.g., `70 MHz`) in the input field and click **Submit Frequency** to visualize the data at that frequency.

- **Continues automatic imaging:**  
   After selecting a frequency, you can continue processing at the same frequency by clicking **Continue Same Frequency**, or continue increasing frequency by cliking **Continue increasing frequency**, then choose a frequency and press **Submit Frequency**

> **Note**
> The Continue increasing frequency mode only will work if the subband is not fixed, this can be cehcked in the .sh file, commenting the line **rspctl --xcsubband=167**.

The program will continue processing your selected frequency option until the end of the `.dat` file.

### 🎬 Creating Observation Videos

You can easily generate a video from your observation images using the `video.py` script:

1. **Navigate to the processor directory:**
   ```bash
   cd realtime_processor
   ```

2. **Run the video script:**
   ```bash
   python3.12 video.py <images_folder> <frequency_number> <fps>
   ```
   - `<images_folder>`: Path to the folder containing your saved images.
   - `<frequency_number>`: The frequency of the observation you want to visualize.
   - `<fps>`: Desired frames per second for the output video.

> **Note**  
> The video will be saved in the same folder that are the images located

This will create a video of your selected frequency observation at your chosen frame rate.

## 📄 License

This project is licensed under the Apache License, Version 2.0.  
See the [LICENSE](./LICENSE) file for full license text.

Original work © ASTRON and contributors.  
Modifications © 2025 Jorge Cuello.
