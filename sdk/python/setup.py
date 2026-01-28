from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agent-factory-sdk",
    version="0.1.0",
    author="Your Organization",
    author_email="platform-team@company.com",
    description="SDK for AI Agent Factory Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/ai-agent-factory-platform",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=[
        "google-cloud-firestore>=2.14.0",
        "google-cloud-logging>=3.8.0",
        "google-cloud-monitoring>=2.18.0",
        "google-cloud-pubsub>=2.19.0",
        "requests>=2.31.0",
        "pydantic>=2.5.0",
        "python-json-logger>=2.0.7",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "pylint>=3.0.0",
            "mypy>=1.7.0",
        ],
    },
)
