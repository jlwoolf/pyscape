import subprocess
import re
import skia
import io

from pathlib import Path
from PIL import Image
from xml.etree import ElementTree as ET
from typing import Any, Tuple, Union, List


class SVG:
    """SVG class to load, edit, render, and export svg files using pillow and inkscape."""

    __WIDTH_HEIGHT_REGEX = "^[1-9]\d*(px|)$|^[1-9]\d*\.?\d*(v(h|w)|\%)$"
    __ICO_SIZES = [16, 32, 48, 64, 256]
    __RESAMPLING_FILTERS = {
        "nearest": 0,
        "lanczos": 1,
        "bilinear": 2,
        "bicubic": 3,
        "box": 4,
        "hamming": 5,
        "rerender": 6
    }

    def __init__(self, fp: Union[str, Path, bytes]):
        """Create an SVG instance from a svg file.

        Args:
            fp (str | Path | bytes): The svg filepath.
        """
        self.root: ET.Element = ET.parse(fp).getroot()
        self.fp: Path = Path(fp).resolve()

    @property
    def size(self) -> Tuple[int, int]:
        """The size of the svg file in pixels. Defaults to (300, 150).
        """
        viewBox = tuple(int(i) for i in self.root.attrib['viewBox'].split(
        )) if 'viewBox' in self.root.attrib else (0, 0, 300, 150)
        width = self.root.attrib['width'] if 'width' in self.root.attrib else "100vw"
        height = self.root.attrib['height'] if 'height' in self.root.attrib else "100vh"

        size = [int(viewBox[2] - viewBox[0]), int(viewBox[3] - viewBox[1])]
        if re.findall("^[1-9]\d*(px|)$", width):
            size[0] = int(re.findall("^[1-9]\d*", width)[0])
        if re.findall("^[1-9]\d*(px|)$", height):
            size[1] = int(re.findall("^[1-9]\d*", height)[0])

        self.root.attrib['viewBox'] = " ".join(str(v) for v in viewBox)
        self.root.attrib['width'] = width
        self.root.attrib['height'] = height

        return tuple(size)

    @property
    def viewBox(self) -> Tuple[int, int, int, int]:
        """The viewBox of the svg file. Defaults to '0 0 300 150'."""
        if 'viewBox' not in self.root.attrib:
            self.root.attrib['viewBox'] = "0 0 300 150"

        return tuple(int(i) for i in self.root.attrib['viewBox'].split())

    @viewBox.setter
    def viewBox(self, value: Tuple[int, int, int, int]):
        """Setter for viewBox."""
        print(" ".join(str(v) for v in value))
        self.root.attrib['viewBox'] = " ".join(str(v) for v in value)

    @property
    def width(self) -> str:
        """The width of the svg. Defaults to 100vw."""
        return self.__get_attrib('width', '100vw')

    @width.setter
    def width(self, value: str) -> str:
        """Setter for width."""
        self.__set_attrib('width', value, __class__.__WIDTH_HEIGHT_REGEX)

    @property
    def height(self) -> str:
        """The width of the svg. Defaults to 100vh."""
        return self.__get_attrib('height', '100vh')

    @height.setter
    def height(self, value: str) -> str:
        """Setter for height."""
        self.__set_attrib('height', value, __class__.__WIDTH_HEIGHT_REGEX)

    def __set_attrib(self, attrib: str, value: str, regex: str = None):
        """Helper function for setting string attributes in the XML tree.

        Args:
            attrib (str): the target attribute.
            value (str): the value to set.
            regex (str | None, optional): A regex str for value checking. Defaults to None.

        Raises:
            ValueError: Value does not satisfy the regex condition.
        """
        if regex and not re.findall(regex, value):
            raise ValueError(
                f"Invalid value for svg attribute {attrib}:", value)

        self.root.attrib[attrib] = value

    def __get_attrib(self, attrib: str, default: Any = None) -> Any:
        """Helper function for getting an svg attribute from the XML tree.

        Args:
            attrib (str): the attribute to return.
            default (Any, optional): The default value of the attribute if it does not exist.

        Returns:
            Any: The attribute value. Will return None if attribute does not exist and no default value was specified.
        """
        if attrib not in self.root.attrib and default:
            if default:
                self.root.attrib[attrib] = default
            else:
                return None

        return self.root.attrib[attrib]

    def __calc_sizes(size: Tuple[int, int], dpi: List[int] = None, sizes: List[Union[int, Tuple[int, int]]] = None) -> List[Tuple[int, int]]:
        """Helper function to calculate the sizes of all images being rendered. Converts DPI values in pixel dimension.

        Args:
            size (Tuple[int, int]): Sizes of the svg.
            dpi (List[int], optional): DPI of the images being rendered. Defaults to None.
            sizes (List[Union[int, Tuple[int, int]]] | None, optional): Sizes of the images being rendered. Defaults to None.

        Returns:
            List[Tuple[int, int]]: A list of sizes (int pairs) of the images being rendered.
        """
        values = list()
        if dpi:
            values.extend(
                [(round(size[0] * (i / 96)), round(size[1] * (i / 96))) for i in dpi])

        if sizes:
            values.extend([i if isinstance(i, tuple) else (i, round(i * size[0]/size[1]))
                          for i in sizes])

        return values

    def __max_size(size: Tuple[int, int], sizes: List[Tuple[int, int]]) -> Tuple[int, int]:
        """Helper function to determine the largest image size to render such that all other sizes are a down scaling of it.

        Args:
            size (Tuple[int, int]): The size of the svg.
            sizes (List[Tuple[int, int]]): The sizes of the images being rendered.

        Returns:
            Tuple[int, int]: A size (int pair) representing the largest necessary image to render.
        """
        max_width, max_height = (max(i) for i in zip(*sizes))
        multi = max(max_width / size[0], max_height / size[1])
        return round(size[0] * multi), round(size[1] * multi)

    def __im_skia(self, dpi = None, size: Union[int, Tuple[int, int]] = None):
        path = Path(self.fp).resolve()

        skia_stream = skia.Stream.MakeFromFile(str(path))
        skia_svg = skia.SVGDOM.MakeFromStream(skia_stream)

        w, h = skia_svg.containerSize()

        if(size):
            sw, sh = size[0], size[1]
        else:
            sw, sh = (dpi / 96) * w, (dpi / 96) * h

        surface = skia.Surface(round(sw), round(sh))
        with surface as canvas:
            canvas.scale(round(sw) / w, round(sh) / h)
            skia_svg.render(canvas)
            
        with io.BytesIO(surface.makeImageSnapshot().encodeToData()) as f:
            img = Image.open(f)
            img.load()
        
        return img

    def __im_inkscape(self, dpi: int = None, size: Union[int, Tuple[int, int]] = None, margin: int = None, area: str = 'page') -> Image.Image:
        """Helper function to render a single PIL.Image object using inkscape.

        Args:
            dpi (int, optional): DPI of the rendered image. Defaults to 96.
            size (Union[int, Tuple[int, int]], optional): Size of the rendered image. Defaults to None.
            margin (int, optional): Margins on the rendered image. Defaults to None.
            area (str, optional): The area to render. Valid values are 'page', 'drawing', and a string of form 'x y w h'. Defaults to 'page'.

        Returns:
            Image.Image: An instance of PIL.Image.Image.
        """
        path = Path(self.fp).resolve()
        options = ["inkscape", "--export-filename=-", "--export-type=png"]

        if area.lower() == 'page':
            options.extend(["--export-area-page"])
        elif area.lower() == 'drawing':
            options.extend(["--export-area-drawing"])
        else:
            options.extend([f"--export-area={area}"])

        if dpi:
            options.extend([f"--export-dpi={dpi}"])

        if size:
            if isinstance(size, int):
                options.extend([f"--export-width={size}"])
            elif not size[1]:
                options.extend([f"--export-width={size[0]}"])
            elif not size[0]:
                options.extend([f"--export-height={size[1]}"])
            else:
                options.extend(
                    [f"--export-width={size[0]}", f"--export-height={size[1]}"])

        if margin:
            options.extend([f"--export-margin={margin}"])

        if not path.exists():
            return None
        else:
            options.extend([f"{path}"])

        pipe = subprocess.Popen(options, stdout=subprocess.PIPE)

        pipe.stdout.readline()
        pipe.stdout.readline()

        return Image.open(pipe.stdout)

    def __im(self, dpi: int = None, size: Union[int, Tuple[int, int]] = None, margin: int = None, area: str = 'page', renderer: str = 'skia'):
        if not dpi and not size:
            dpi = 96
        
        if renderer == 'skia':
            return self.__im_skia(dpi, size)
        elif renderer == 'inkscape':
            return self.__im_inkscape(dpi, size, margin, area)

        else:
            raise ValueError(
                "Invalid renderer. Only support renderers are 'skia' and 'inkscape'")

    def __im_multi(self, dpi: List[int] = None, sizes: List[Union[int, Tuple[int, int]]] = None, margin: int = None, area: str = 'page', filter: str = "lanczos", renderer: str = "skia") -> List[Image.Image]:
        """Helper function to generate images of multiple specified sizes.

        Args:
            dpi (List[int], optional): DPI's of the images to render. Defaults to None.
            sizes (List[Union[int, Tuple[int, int]]], optional): Sizes of the images to render. Defaults to None.
            margin (int, optional): Margin of the images (shared across all). Defaults to None.
            area (str, optional): The area to render. Valid values are 'page', 'drawing', and a string of form 'x y w h'. Defaults to 'page'.
            filter (str, optional): Which filter to use for to downscale. Use 'rerender' to render each image individual at desired size. Defaults to 'lanczos'.

        Raises:
            ValueError: No DPI's or sizes are specified.
            ValueError: Filter is invalid.

        Returns:
            List[Image.Image]: A list of PIL.Image.Image instances of different sizes.
        """
        if not dpi and not sizes:
            raise ValueError(
                "Must specify either multiple dpi, sizes, or both")

        if filter not in __class__.__RESAMPLING_FILTERS:
            raise ValueError(
                f"Invalid filter: {filter}\nValid filters are: {' '.join(__class__.__RESAMPLING_FILTERS.keys())}")

        sizes = __class__.__calc_sizes(self.size, dpi, sizes)
        if filter == "rerender":
            return list(self.__im(size=size, margin=margin, area=area, renderer=renderer) for size in sizes)
        else:
            img = self.__im(size=__class__.__max_size(
                self.size, sizes), margin=margin, area=area, renderer=renderer)
            return list(img.resize(size, __class__.__RESAMPLING_FILTERS[filter.lower()]) for size in sizes)

    def __export(img: Image.Image, stem: str = None, format: Union[str, List[str]] = "png"):
        """Helper function to export a PIL.Image.Image instance to another image format.

        Args:
            img (Image.Image): The image to export.
            stem (str, optional): The name/path of the image (without the extension). Defaults to None.
            format (str | List[str], optional): The formats to export. Defaults to "png".
                Valid formats are defined here: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html\n

        Raises:
            FileNotFoundError: The target directory for exporting does not exist.
        """
        if isinstance(format, str):
            format = [format]

        parent = Path(stem).resolve().parent
        if not parent.is_dir():
            raise FileNotFoundError(
                f"Could not locate the directory: {parent}\nPlease make sure the directory exists")

        for f in format:
            if f == "ico":
                img.save(f"{stem}.{f}", sizes=[
                         (i, i) for i in __class__.__ICO_SIZES if i < img.width and i < img.height])
                continue
            try:
                img.save(f"{stem}.{f}")
            except OSError:
                img.convert("RGB").save(f"{stem}.{f}")

    def __export_multi(img: List[Image.Image], stem: str = None, format: Union[str, List[str]] = "png"):
        """Helper function to export multiple images in different formats.

        Args:
            img (List[Image.Image]): A list of images to export.
            stem (str, optional): The name/path of the image (without the extension). Defaults to None.
            format (str | List[str], optional): The formats to export. Defaults to "png".
                Valid formats are defined here: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html\n
        """
        for i in img:
            __class__.__export(i, f"{stem}_{i.size[0]}_{i.size[1]}", format)

    def im(self, dpi: Union[int, List[int]] = None, size: List[Union[int, Tuple[int, int]]] = None, margin: int = None, area: str = 'page', filter: str = "lanczos", renderer: str = "skia") -> Union[Image.Image, List[Image.Image]]:
        """
        Render the SVG as PIL.Image instance.

        Args:
            dpi (int | List[int], optional): The DPI(s) to render the image(s) at. Defaults to 96.
            size (List[Union[int, Tuple[int, int]]], optional): The size(s) to render the image(s) at. 
            Can be a single integer (defining the width) or a pair for width and height. Defaults to None.
            margin (int, optional): Margin of the images (shared across all). Defaults to None.
            area (str, optional): The area to render. Valid values are 'page', 'drawing', and a string of form 'x y w h'. Defaults to 'page'.
            filter (str, optional): Which filter to use for to downscale. Use 'rerender' to render each image individual at desired size. Defaults to 'lanczos'.

        Returns:
            Union[Image.Image, List[Image.Image]]: _description_
        """
        if (dpi and size) or (isinstance(dpi, list) and len(dpi) > 1) or (isinstance(size, list) and len(size) > 1):
            return self.__im_multi(dpi, size, margin, area, filter, renderer=renderer)
        elif isinstance(dpi, list):
            return self.__im(dpi[0], size, margin, area, renderer=renderer)
        elif isinstance(size, list):
            return self.__im(dpi, size[0], margin, area, renderer=renderer)

        return self.__im(dpi, size, margin, area)

    def save(self, fp: Union[str, Path, bytes] = None):
        """Saves the SVG XML tree.

        Args:
            fp (str | Path | bytes, optional): The save path. If no path is specified, this will overwrite the original SVG. Defaults to None.
        """
        if fp is None:
            fp = self.fp
        else:
            fp = Path(fp).resolve()

        ET.ElementTree(self.root).write(fp)

    def export(self, stem: str = None, format: Union[str, List[str]] = "png", dpi: Union[int, List[int]] = 96, size: List[Union[int, Tuple[int, int]]] = None, margin: int = None, area: str = 'page', filter: str = "lanczos", renderer: str = "skia"):
        """Renders and exports image(s) of specified size(s) as specified format(s).

        Args:
            stem (str, optional): The name/path of the image (without the extension). Defaults to None.
            format (str | List[str], optional): The formats to export. Defaults to "png".
                Valid formats are defined here: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html\n
            dpi (int | List[int], optional): The DPI(s) to render the image(s) at. Defaults to 96.
            size (List[Union[int, Tuple[int, int]]], optional): The size(s) to render the image(s) at. 
            Can be a single integer (defining the width) or a pair for width and height. Defaults to None.
            margin (int, optional): Margin of the images (shared across all). Defaults to None.
            area (str, optional): The area to render. Valid values are 'page', 'drawing', and a string of form 'x y w h'. Defaults to 'page'.
            filter (str, optional): Which filter to use for to downscale. Use 'rerender' to render each image individual at desired size. Defaults to 'lanczos'.
        """
        if not stem:
            stem = self.fp.stem

        img = self.im(dpi, size, margin, area, filter, renderer=renderer)
        if isinstance(img, list) and len(img) > 1:
            __class__.__export_multi(img, stem, format)
        elif isinstance(img, list):
            __class__.__export(img[0], stem, format)
        else:
            __class__.__export(img, stem, format)

    @classmethod
    def IM(cls, fp: Union[str, Path, bytes], dpi: int = 96, size: Union[int, Tuple[int, int]] = None, margin: int = None, area: str = 'page', renderer: str = 'skia'):
        """Classmethod that returns a PIL.Image instance of a specified SVG. Useful if you do not need to create a class object.

        Args:
            fp (str | Path | bytes): The path of the svg file.
            dpi (int, optional): DPI of the rendered image. Defaults to 96.
            size (Union[int, Tuple[int, int]], optional): Size of the rendered image. Defaults to None.
            margin (int, optional): Margins on the rendered image. Defaults to None.
            area (str, optional): The area to render. Valid values are 'page', 'drawing', and a string of form 'x y w h'. Defaults to 'page'.

        Returns:
            _type_: _description_
        """
        return cls(fp).im(dpi, size, margin, area, renderer)

    @classmethod
    def EXPORT(cls, fp: Union[str, Path, bytes], stem: str = None, format: Union[str, List[str]] = "png", dpi: int = 96, size: Union[int, Tuple[int, int]] = None, margin: int = None, area: str = 'page', filter="lanczos", renderer: str = "skia"):
        """Classmethod that renders an SVG and exports image(s) of specified size(s) as specified format(s). Useful if you do not need to create an SVG class object.

        Args:
            fp (str | Path | bytes): The path of the svg file.
            stem (str, optional): The name/path of the image (without the extension). Defaults to None.
            format (str | List[str], optional): The formats to export. Defaults to "png".
                Valid formats are defined here: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html\n
            dpi (int | List[int], optional): The DPI(s) to render the image(s) at. Defaults to 96.
            size (List[Union[int, Tuple[int, int]]], optional): The size(s) to render the image(s) at. 
            Can be a single integer (defining the width) or a pair for width and height. Defaults to None.
            margin (int, optional): Margin of the images (shared across all). Defaults to None.
            area (str, optional): The area to render. Valid values are 'page', 'drawing', and a string of form 'x y w h'. Defaults to 'page'.
            filter (str, optional): Which filter to use for to downscale. Use 'rerender' to render each image individual at desired size. Defaults to 'lanczos'.
        """
        cls(fp).export(stem, format, dpi, size, margin, area, filter, renderer)
