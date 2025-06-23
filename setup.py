from setuptools import setup, find_packages

setup(
    name="json-loader-with-include",
    version="0.3.3",
    url="https://github.com/PypayaTech/json-loader-with-include",
    author="PypayaTech",
    description="⚠️ DEPRECATED: Use 'pypaya-json' instead. Enhanced JSON processing with includes.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    readme="README.md",
    license="MIT",
    packages=find_packages(),
    extras_require={
        "test": ["pytest"],
    }
)
