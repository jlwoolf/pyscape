import os
import argparse
import pathlib

from typing import List, Tuple
from tqdm import tqdm
from pyscape import svg2im
from dataclasses import dataclass

ICO_SIZES = [16, 32, 48, 64, 256]
RESAMPLING_FILTERS = {
    "nearest": 0,
    "lanczos": 1,
    "bilinear": 2,
    "bicubic": 3,
    "box": 4,
    "hamming": 5,
    "rerender": 6
}


@dataclass
class __Args:
    gui: bool = None
    count: int = None
    verbose: int = None
    max_value: int = None
    max_index: int = None
    dir: str = None
    scaling: str = None
    out: str = None
    svg: str = None
    format: List[str] = None
    dpi: List[int] = None
    dim: List[int] = None
    size: List[int] = None
    sizes: List[Tuple[int, int]] = None
    tqdm: tqdm = None
    


def __setup_parser_default(parser: argparse.ArgumentParser):
    parser.add_argument('--gui', action="store_true", default=False, help="Currently does not work, please do not this use flag.")
    parser.add_argument('--dir', type=str, nargs="?",
                        default=os.getcwd(), help="The directory to search for svg's. Default directory is the current working directory.")
    parser.add_argument("--format", "-f", metavar='F', type=str, nargs='+', default=['png'],
                        help="The formats to export. Supported formats are outlined here: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html")
    parser.add_argument("--scaling", "-s", metavar='S', type=str, nargs='?', default="lanczos",
                        help="Scaling method to use. The options in order from fastest to slowest are: nearest, lanczos, bilinear, bicubic, box, hamming, rerender. Quality will decrease with performance.")
    mut_group = parser.add_mutually_exclusive_group()

    mut_group.add_argument("--dpi", type=int, nargs='*', default=[96],
                           help="The dpi's of the output images. If more than one value specified, output images of 'example.svg' will come in the form of 'example_96dpi.png'.")
    mut_group.add_argument('--dim', type=int, nargs='*', default=list(),
                           help="The dimensions of the output images (width height). If more than one value is specified, the output images of 'example.svg' will come in the form of 'example_500_300.png'.")
    mut_group.add_argument('--size', metavar='sz', type=int, nargs='*', default=list(),
                           help="The size (width) of the output images. If more than one value is specified, the output images of 'example.svg' will come in the form of 'example_500.png'.")
    parser.add_argument("--verbose", "-v", action='count', default=0,
                        help="The verbosity of the progress output. By default there is no output.")


def __setup_parser_file(parser: argparse._SubParsersAction):

    parser_file = parser.add_parser(
        'file', help="Convert a single SVG file to an image format")

    parser_file.add_argument("svg", type=str,
                             help="Path to the svg file to convert")

    parser_file.add_argument("--out", "-o", type=str,
                             help="Name/prefix of the output files.")

    parser_file.add_argument("--format", "-f", metavar='F', type=str, nargs='+', default=['png'],
                             help="The formats to export. Supported formats are outlined here: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html")
    parser_file.add_argument("--scaling", "-s", metavar='S', type=str, nargs='?', default="lanczos",
                             help="Scaling method to use. The options in order from fastest to slowest are: nearest, lanczos, bilinear, bicubic, box, hamming, rerender. Quality will decrease with performance.")
    mut_group = parser_file.add_mutually_exclusive_group()

    mut_group.add_argument("--dpi", type=int, nargs='*', default=[96],
                           help="The dpi's of the output images. If more than one value specified, output images of 'example.svg' will come in the form of 'example_96dpi.png'.")
    mut_group.add_argument('--dim', type=int, nargs='*', default=list(),
                           help="The dimensions of the output images (width height). If more than one value is specified, the output images of 'example.svg' will come in the form of 'example_500_300.png'.")
    mut_group.add_argument('--size', metavar='sz', type=int, nargs='*', default=list(),
                           help="The size (width) of the output images. If more than one value is specified, the output images of 'example.svg' will come in the form of 'example_500.png'.")
    parser_file.add_argument("--verbose", "-v", action='count', default=0,
                             help="The verbosity of the progress output. By default there is no output.")


# def setup_parser_json(parser: argparse._SubParsersAction):
#     parser_json = parser.add_parser(
#         'json', help="Convert multiple SVG files to PNG and/or ICO files")
#     parser_json.add_argument(
#         "json-file", type=str, help="a json file containing input and output filenames")
#     parser_json.add_argument('--ico-sizes', metavar='Is', type=int, nargs='*', default=[16, 32, 48, 64, 256],
#                              help='default ico file sizes if not specified in json')
#     parser_json.add_argument('--png-sizes', metavar='Ps', type=int, nargs='*', default=[512],
#                              help='default png file sizes if not specified in json')
#     parser_json.add_argument("--verbose", "-v", action='store_true',
#                              help="print progress statements")
#     parser_json.add_argument("--force", "-f", action='store_true',
#                              help="default overwrite if not specified in json")

def __get_sizes(args: __Args):
    if args.dim:
        try:
            assert(len(args.dim) % 2 == 0)
        except AssertionError:
            print("Must be an even number of --dim arguments")
            print("Number of arguments passed:", len(args.dim))

        args.sizes = [(args.dim[i * 2], args.dim[i*2 + 1])
                      for i in range(int(len(args.dim) / 2))]

    elif args.size:
        args.sizes = [(i, i) for i in args.size]

def __get_max(args: __Args):
    if args.sizes:
        widths = [i[0] for i in args.sizes]
        heights = [i[0] for i in args.sizes]
        max_width = max(widths)
        max_height = max(heights)

        args.max_value = (None, max_height) if max_height > max_width else (
            max_width)
        args.max_index = heights.index(
            max_height) if max_height > max_width else widths.index(max_width)

        args.count = len(args.sizes)
    else:
        args.max_value = max(args.dpi)
        args.max_index = args.dpi.index(max(args.dpi))

        args.count = len(args.dpi)


def __convert_svg(args: __Args, svg_path: pathlib.Path):
    imgs = []

    if args.out:
        svg_stem = args.out
    else:
        svg_stem = svg_path.stem

    if args.scaling == 'rerender':
        if args.sizes:
            for size in args.sizes:
                imgs.append(svg2im(svg_path, size=size))
                args.tqdm.update()
            paths = [f"{svg_stem}_{size[0]}" if size[0] == size[1]
                     else f"{svg_stem}_{size[0]}_{size[0]}" for size in args.sizes]
        else:
            for dpi in args.dpi:
                imgs.append(svg2im(svg_path, dpi=dpi))
                args.tqdm.update()

            paths = [f"{svg_stem}_{dpi}dpi" for dpi in args.dpi]

    else:
        if args.sizes:
            img = svg2im(svg_path, size=args.max_value)
            for size in args.sizes:
                imgs.append(img.resize(
                    size, RESAMPLING_FILTERS[args.scaling.lower()]))
                args.tqdm.update()
            
            paths = [f"{svg_stem}_{size[0]}" if size[0] == size[1]
                     else f"{svg_stem}_{size[0]}_{size[0]}" for size in args.sizes]
        else:
            img = svg2im(svg_path, dpi=args.max_value)
            for dpi in args.dpi:
                imgs.append(img.resize((int(img.size[0] * dpi/args.max_value), int(
                    img.size[0] * dpi/args.max_value)), RESAMPLING_FILTERS[args.scaling.lower()]))
                args.tqdm.update()
            paths = [f"{svg_stem}_{dpi}dpi" for dpi in args.dpi]

    if len(imgs) == 1:
        for format in args.format:
            if format == 'ico':
                imgs[0].save(f"{svg_stem}.{format}", sizes=[
                    (i, i) for i in ICO_SIZES if imgs[0].size[0] > i and imgs[0].size[1] > i])
            else:
                try:
                    imgs[0].save(f"{svg_stem}.{format}")
                except OSError:
                    imgs[0].convert("RGB").save(
                        f"{svg_stem}.{format}")
    else:
        for i, (img, path) in enumerate(zip(imgs, paths)):
            for format in args.format:
                if format == 'ico' and i == args.max_index:
                    img.save(f"{svg_stem}.{format}", sizes=[
                        (i, i) for i in ICO_SIZES if img.size[0] > i and img.size[1] > i])
                elif format != 'ico':
                    try:
                        img.save(f"{path}.{format}")
                    except OSError:
                        img.convert("RGB").save(
                            f"{path}.{format}")


def __command_line(args: __Args):
    args.dir = pathlib.Path(args.dir)

    __get_sizes(args)
    __get_max(args)

    if args.svg:
        svg_paths = [pathlib.Path(args.svg)]
    else:
        svg_paths = list(args.dir.glob("*.svg"))

    args.tqdm = tqdm(total=len(svg_paths) * args.count)
    for svg_path in svg_paths:
        __convert_svg(args, svg_path)


def main():
    parser = argparse.ArgumentParser("pyscape", description="""
    Converts svg files to different image formats utilizing pillow and inkscape. By default, pyscape will convert
    all svg files from the current working directory to the specified image format. For example if the svg file is 
    'example.svg', then 'pyscape --f png' will create file 'example.png'.""")

    __setup_parser_default(parser)
    subparsers = parser.add_subparsers(title="Convert a single SVG")
    __setup_parser_file(subparsers)
    # setup_parser_json(subparsers)

    args = __Args(**vars(parser.parse_args()))
    if(args.gui):
        pass
    else:
        __command_line(args)
