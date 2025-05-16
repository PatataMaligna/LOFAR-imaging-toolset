from setuptools import setup, find_packages

setup(
    name="lofarimaging",
    version="1.0.0",
    description="Real-time data processing for LOFAR single station imaging",
    author="Jorge Cuello Tejero",
    author_email="jorgecuellod18@gmail.com",
    url="https://github.com/PatataMaligna/LOFAR-imaging-toolset",
    packages=find_packages(),
    install_requires=[
        "numpy>=2.0.0",
        "matplotlib>=3.10.3",
        "astropy>=7.0.1",
        "packaging>=24.1",
        "h5py>=3.13.0",
        "lofarantpos>=0.7.1",
        "numba>=0.61.0",
        "numexpr>=2.10.2",
        "opencv-python>=4.10.0.84",
        "PyQt6>=6.9.0",
        "tqdm>=4.67.1",
    ],
    entry_points={
        "console_scripts": [
            "realtime-processor=realtime_processor.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    license="Apache-2.0",
)
