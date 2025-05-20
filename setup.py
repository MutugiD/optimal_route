from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="route-optimizer",
    version="0.1.0",
    author="Dennis Mutugi",
    author_email="dennismutugi@gmail.com",
    description="A Django-based API for optimal fuel stop planning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/fuel-planner",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Framework :: Django",
        "Framework :: Django :: 3.2.23",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "route-optimizer=optimal_api.manage:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)