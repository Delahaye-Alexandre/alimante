from setuptools import setup, find_packages

setup(
    name="alimante",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'fastapi>=0.104.0',
        'uvicorn>=0.24.0',
        'websockets>=12.0',
        'sqlalchemy>=2.0.0',
        'pydantic>=2.5.0',
        'RPi.GPIO>=0.7.0',
        'adafruit-circuitpython-dht>=3.7.0',
        'schedule>=1.1.0',
        'astral>=3.2',
        'requests>=2.31.0',
        'pytest>=7.0.0',
        'pytest-mock>=3.10.0',
        'pytest-asyncio>=0.21.0',
        'python-dotenv>=1.0.0',
    ],
    author="Alexandre Delahaye",
    author_email="alexandre-delahaye@outmlook.fr",
    description="Système de gestion automatisé pour l'élevage de mantes avec Raspberry Pi",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Linux Raspbian",
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'alimante=main:main',
        ],
    },
)