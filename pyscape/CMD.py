
import argparse


def main():
    parser = argparse.ArgumentParser("pyscape", description="""
Converts svg files to different image formats utilizing pillow and inkscape. By default, pyscape will convert
all svg files from the current working directory to the specified image format. For example if the svg file is 
'example.svg', then 'pyscape --f png' will create file 'example.png'.
        """)
