from setuptools import setup, find_packages

setup(
    name="git-dvc-bridge",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "dvc",
    ],
    entry_points={
        "console_scripts": [
            "git-dvc-bridge=git_dvc_bridge.cli:main",
        ],
    },
    author="Terry",
    author_email="teri04111@gmail.com",
    description="A bridge between Git and DVC for automatic data versioning",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/teri0411/git-dvc-bridge",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
