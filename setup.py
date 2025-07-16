from setuptools import setup, find_packages

setup(
    name="approximator",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'numpy',
        'pandas',
        'PyQt5',
    ],
)
