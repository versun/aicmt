from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize
import os
import glob

# 读取版本号
with open("aicmt/__version__.py", "r") as f:
    exec(f.read())

# 读取README
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

# 查找所有需要编译的.py文件
extensions = []
for py_file in glob.glob("aicmt/**/*.py", recursive=True):
    if not py_file.endswith('__init__.py') and not py_file.endswith('__version__.py'):
        extension_name = os.path.splitext(py_file)[0].replace(os.path.sep, '.')
        extensions.append(Extension(extension_name, [py_file]))

setup(
    name="aicmt",
    version=VERSION,
    description="An intelligent Git commit assistant that not only generates commit messages, but also automatically analyzes and splits your code changes into multiple well-organized commits following best practices.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Versun",
    author_email="aicmt@versun.me",
    maintainer="Versun",
    maintainer_email="aicmt@versun.me",
    url="https://github.com/versun/aicmt",
    project_urls={
        "Homepage": "https://github.com/versun/aicmt",
        "Repository": "https://github.com/versun/aicmt.git",
        "Issues": "https://github.com/versun/aicmt/issues",
    },
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.10",
    install_requires=[
        "gitpython",
        "openai",
        "rich",
        "cython",  # 添加Cython依赖
    ],
    extras_require={
        "dev": [
            "ruff",
            "pytest",
        ],
    },
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            'language_level': "3",
            'boundscheck': False,
            'wraparound': False,
            'initializedcheck': False,
        }
    ),
    entry_points={
        "console_scripts": [
            "aicmt=aicmt.cli:cli",
        ],
    },
    license="MIT",
    keywords=[
        "aicmt", "ai commit", "ai git commit", "git", "commit", "message",
        "change", "code", "ai", "intelligence", "intelligent", "automated", "assistant"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Version Control :: Git",
    ],
)