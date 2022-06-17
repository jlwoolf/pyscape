from setuptools import setup, find_packages
import pathlib

dir = pathlib.Path(__file__).parent.resolve()
long_description = (dir / "README.md").read_text(encoding="utf-8")

setup (
    name="pyscape",
    version="1.0.0",
    description="a library and command line utility for using SVG files with pillow",
    long_description=long_description,
    url="",
    author="jlwoolf",
    author_email="jlwoolf@proton.me",
    packages=['pyscape'],
    install_requires=['pillow', 'skia-python'],
    license='MIT',
    keywords="svg, inkscape, pillow",
    # entry_points={
    #         'console_scripts': ['pyscape=pyscape.command_line:main']
    # }
)