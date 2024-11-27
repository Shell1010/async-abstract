from setuptools import setup, find_packages

setup(
    name="async_abstract",
    version="0.1.0",
    description="A package that provides abstract base classes for async functionality",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author="Shell1010",
    author_email="amin.dev03@gmail.com",
    url="https://github.com/shell1010/async-abstract",
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
