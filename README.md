# 🌌 LOFAR Imaging Toolset

> A real-time data processing tool for **LOFAR** single-station observations

---

## ⚙️ Installation

1. **Clone repository**

   ```bash
   git clone https://github.com/lofar-astron/LOFAR-imaging-toolset.git
   cd LOFAR-imaging-toolset
   ```

2. **Setup Python venv**

   ```bash
   python3 -m venv envLofar
   source envLofar/bin/activate
   ```

3. **Install system deps**

   ```bash
   sudo apt update && sudo apt install -y libgl1 libglib2.0-0
   ```

4. **Install Python deps**

   ```bash
   pip install git+https://github.com/lofar-astron/lofarimaging.git
   cd realtime_processor
   pip install -r requirements.txt
   ```

5. **Run processor**

   > **Note:**  
   > You must run the command from the `lofarimaging` folder (the parent of `realtime_processor`), **not** from inside the `realtime_processor` directory.  
   > This ensures Python can find the package and all imports work correctly.
   ```bash
   cd ..
   python3 -m realtime_processor.main /path/to/your/data
   ```

---

## 🚀 Usage
```bash
python3 -m realtime_processor.main /your/data/path
```

## 📄 License

MIT © LOFAR Astron
