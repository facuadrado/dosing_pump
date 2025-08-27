from setuptools import setup, find_packages

setup(
    name="dosing_pump",
    version="0.1.0",
    description="A dosing pump client using sqlite3 and FastAPI",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "RPi.GPIO",
        "apscheduler",
    ],
    python_requires=">=3.7",
)