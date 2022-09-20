from setuptools import setup
import pathlib

dir = pathlib.Path(__file__).parent.resolve()
long_description = (dir / "README.md").read_text(encoding="utf-8")

setup (
    name="pillow-svg",
    version="1.0.1",
    description="a library and command line utility for using SVG files with pillow",
    long_description=long_description,
    url="",
    author="jlwoolf",
    author_email="jlwoolf@proton.me",
    packages=['PILSVG'],
    install_requires=['pillow', 'skia-python'],
    license='MIT',
    keywords="svg, inkscape, pillow",
    test_suite='nose.collector',
    tests_require=['nose'],
    entry_points={
            'console_scripts': ['pillow-svg=PILSVG.CMD:main']
    }
)
