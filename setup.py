from setuptools import setup, find_packages

setup(
    name="json-loader-with-include",
    version="0.1.0",
    url="https://github.com/PypayaTech/json-loader-with-include",
    author="PypayaTech",
    description="A simple package that allows you to include (fragments of) external JSON files within a JSON file.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    readme="README.md",
    license="MIT",
    packages=find_packages(),
    extras_require={
        "test": ["pytest"],
    }
)
