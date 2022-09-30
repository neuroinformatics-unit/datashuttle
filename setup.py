from os import path

from setuptools import find_packages, setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

requirements = []


setup(
    name="project_manager_swc",
    version="0.0.0",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=requirements,
    extras_require={
        "dev": [
            "black",
            "pytest-cov",
            "pytest",
            "coverage",
            "bump2version",
            "pre-commit",
            "flake8",
        ]
    },
    python_requires=">=3.7",
    packages=find_packages(),
    #    entry_points={"console_scripts": ["brainreg = brainreg.cli:main"]},
    include_package_data=True,
    author="Joe Ziminski",
    author_email="joseph.j.ziminski@gmail.com",
    classifiers=[""],
    zip_safe=False,
)
