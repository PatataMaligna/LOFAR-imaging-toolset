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
        "numpy",
        "matplotlib",
        "astropy",
        "packaging"
    ],
    entry_points={
        "console_scripts": [
            "realtime-processor=realtime_processor.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)