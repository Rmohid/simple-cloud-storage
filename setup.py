from setuptools import setup, find_packages

setup(
    name="simple-cloud-storage",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'flask',
        'flask-jwt-extended',
        'pymongo',
        'python-magic',
        'python-dotenv'
    ],
    python_requires='>=3.12',
)