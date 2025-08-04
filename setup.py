from setuptools import setup, find_packages

setup(
    name="mantcare",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pyserial>=3.5',
        'schedule>=1.1.0',
        'astral>=3.2',  # Pour le calcul du coucher du soleil
        'pytest>=7.0.0',  # Pour les tests
        'pytest-mock>=3.10.0',  # Pour les mocks dans les tests
        # 'logging>=0.5.1.2',  # Problème: logging est un module standard
    ],
    author="Alexandre Delahaye",
    author_email="alexandre-delahaye@outmlook.fr",
    description="Système de gestion automatisé pour l'élevage de mantes",
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
            'mantcare=main:main',
        ],
    },
)