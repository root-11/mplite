from setuptools import setup

with open(str("README.md"), encoding='utf-8') as f:
    long_description = f.read()

keywords = list({
    'multiprocessing', 'tasks'
})

keywords.sort(key=lambda x: x.lower())

with open('requirements.txt', 'r') as fi:
    requirements = [v.rstrip('\n') for v in fi.readlines()]

with open('mplite/__init__.py', 'r') as fi:
    for line in fi.readlines():
        if line.startswith("major, minor, patch"):  # something like """major, minor, patch = 1, 1, 0"""
            exec(line)  # creates variables major, minor, patch
            __version_info__ = (major, minor, patch)
            version = '.'.join(str(i) for i in __version_info__)
            break

setup(
    name="mplite",
    version=version,
    url="https://github.com/root-11/mplite",
    license="MIT",
    author="root-11",
    description="A module that makes multiprocessing easy.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=keywords,
    packages=["mplite"],
    include_package_data=True,
    data_files=[(".", ["LICENSE", "README.md", "requirements.txt"])],
    platforms="any",
    install_requires=requirements,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)

