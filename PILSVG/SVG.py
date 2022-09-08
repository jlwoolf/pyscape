import subprocess
import re
import skia
import io

from platform import system
from pathlib import Path
from PIL import Image
from xml.etree import ElementTree as ET
from typing import Any, Tuple, Union, List



class SVG:
    """SVG class to load, edit, render, and export svg files using pillow and inkscape."""

    if system() == "Darwin":
        __SYSTEM_DPI = 72
    else:
        __SYSTEM_DPI = 96

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

        # Check if filepath is valid
        self.fp: Path = Path(fp).resolve()
        if not self.fp.exists():
            raise FileNotFoundError(f"SVG file '{fp}' does not exist.")
        
        # Load SVG xml file
        self.root: ET.Element = ET.parse(fp).getroot()

    def __str_to_nu(self, input: str) -> Tuple[float, str]:
        """Extracts size number and units from string.

        Args:
            input (str): String in the form of '{number}{units}'. Accepts strings containing integers and floats.
        
        Returns:
            Tuple[float, str]: The number and unit values.
        """
        unit = re.findall("(|mm|px|in|vw|\%)$", input)[0]
        num = float(re.findall("^([1-9]\d*\.?\d*|[1-9]\d*)", input)[0])
        return num, unit

    def __to_px(self, num: float, unit: str, view: Tuple[float, float] = None) -> int:
        """Converts a number of unit types mm, cm, in, vw, vh, and % to pixels.

        Args:
            number (float): The number to convert to pixels
            unit (str): The unit of the number for conversion. Currently supports mm, cm, in, vw, vh, and %.
            view (Tuple[float, float]): The svg view box dimensions for units of vw, vh, and %.
        
        Raises:
            ValueError: View box is not provided for units of vw, vh, and %.

        Returns:
            int: The number converted to pixel units.
        """
        

        if unit == 'mm':
            num *= (__class__.__SYSTEM_DPI / 25.4)
        if unit == 'cm':
            num *= (__class__.__SYSTEM_DPI / 2.54)
        elif unit == 'in':
            num *= __class__.__SYSTEM_DPI

        if unit in ["%", "vw", "vh"]:
            if not view:
                raise ValueError(f"View box is necessary for conversions involving {unit}'s")

            sw, sh = view
            if unit == "vh":
                num *= sh / 100.
            else:
                num *= sw / 100.                
            
        return str(num), unit

    @property
    def size(self) -> Tuple[int, int]:
        """The size of the svg file in pixels. Defaults to (300, 150).
        """
        viewBox = tuple(float(i) for i in self.root.attrib['viewBox'].split(
        )) if 'viewBox' in self.root.attrib else (0, 0, 300, 150)
        width = self.root.attrib['width'] if 'width' in self.root.attrib else "100vw"
        height = self.root.attrib['height'] if 'height' in self.root.attrib else "100vh"

        sw, sh = float(viewBox[2] - viewBox[0]), float(viewBox[3] - viewBox[1])
        _, uw = self.__str_to_nu(width)
        _, uh = self.__str_to_nu(height)
        
        if uw in ["mm", "in", "cm"]:
            sw = self.__to_px(sw, uw)
        if uh in ["mm", "in", "cm"]:
            sh = self.__to_px(sh, uh)

        return int(sw), int(sh)

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

    def __calc_sizes(self, dpi: List[int] = None, sizes: List[Union[int, Tuple[int, int]]] = None) -> List[Tuple[int, int]]:
        """Helper function to calculate the sizes of all images being rendered. Converts DPI values in pixel dimension.

        Args:
            dpi (List[int], optional): DPI of the images being rendered. Defaults to None.
            sizes (List[Union[int, Tuple[int, int]]] | None, optional): Sizes of the images being rendered. Defaults to None.

        Returns:
            List[Tuple[int, int]]: A list of sizes (int pairs) of the images being rendered.
        """
        sw, sh = self.size

        if not dpi and not sizes:
            values = [(sw, sh)]
        else:
            values = []
            if dpi:
                values.extend(
                    [(round(sw * (i / __class__.__SYSTEM_DPI)), round(sh * (i / __class__.__SYSTEM_DPI))) for i in dpi])
            if sizes:
                values.extend([i if isinstance(i, tuple) else (
                    i, round(i * sh/sw)) for i in sizes])

        return values

    def __max_size(self, sizes: List[Tuple[int, int]]) -> Tuple[int, int]:
        """Helper function to determine the largest image size to render such that all other sizes are a down scaling of it.

        Args:
            sizes (List[Tuple[int, int]]): The sizes of the images being rendered.

        Returns:
            Tuple[int, int]: A size (int pair) representing the largest necessary image to render.
        """
        sw, sh = self.size

        max_width, max_height = (max(i) for i in zip(*sizes))
        multi = max(max_width / sw, max_height / sh)
        return round(sw * multi), round(sh * multi)
    
    def __im_skia(self, size: Tuple[int, int]) -> Image.Image:
        """Helper function to render a single PIL.Image object using skia-python.

        Args:
            size (Union[int, Tuple[int, int]], optional): Size of the rendered image.

        Returns:
            Image.Image: An instance of PIL.Image.Image.
        """
        path = Path(self.fp).resolve()

        skia_stream = skia.Stream.MakeFromFile(str(path))
        skia_svg = skia.SVGDOM.MakeFromStream(skia_stream)

        w, h = skia_svg.containerSize()
        sw, sh = size

        surface = skia.Surface(round(sw), round(sh))
        with surface as canvas:
            canvas.scale(round(sw) / w, round(sh) / h)
            skia_svg.render(canvas)

        with io.BytesIO(surface.makeImageSnapshot().encodeToData()) as f:
            img = Image.open(f)
            img.load()

        return img

    def __im_inkscape(self, size: Tuple[int, int], margin: int = None, area: str = 'page') -> Image.Image:
        """Helper function to render a single PIL.Image object using inkscape.

        Args:
            size (Union[int, Tuple[int, int]], optional): Size of the rendered image.
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

        sw, sh = size
        if size:
            options.extend([f"--export-width={sw}", f"--export-height={sh}"])

        if margin:
            options.extend([f"--export-margin={margin}"])

        if not path.exists():
            return None
        else:
            options.extend([f"{path}"])

        try:
            pipe = subprocess.Popen(options, stdout=subprocess.PIPE)
        except FileNotFoundError:
            raise FileNotFoundError("Please make sure inkscape has been added to path")

        pipe.stdout.readline()
        pipe.stdout.readline()

        return Image.open(pipe.stdout)

    def __im(self, size: Tuple[int, int], margin: int = None, area: str = 'page', renderer: str = 'skia') -> Image.Image:
        """Helper function to choose proper renderer. Throws an error if the renderer is not supported.
        """

        if renderer == 'skia':
            return self.__im_skia(size)
        elif renderer == 'inkscape':
            return self.__im_inkscape(size, margin, area)

        else:
            raise ValueError(
                "Invalid renderer. Only supported renderers are 'skia' and 'inkscape'")

    def __im_multi(self, sizes: List[Tuple[int, int]], margin: int = None, area: str = 'page', filter: str = "lanczos", renderer: str = "skia") -> List[Image.Image]:
        """Helper function to generate images of multiple specified sizes.

        Args:
            sizes (List[Union[int, Tuple[int, int]]], optional): Sizes of the images to render.
            margin (int, optional): Margin of the images (shared across all). Defaults to None.
            area (str, optional): The area to render. Valid values are 'page', 'drawing', and a string of form 'x y w h'. Defaults to 'page'.
            filter (str, optional): Which filter to use for to downscale. Use 'rerender' to render each image individual at desired size. Defaults to 'lanczos'.

        Raises:
            ValueError: Filter is invalid.

        Returns:
            List[Image.Image]: A list of PIL.Image.Image instances of different sizes.
        """
        if filter not in __class__.__RESAMPLING_FILTERS:
            raise ValueError(
                f"Invalid filter: {filter}\nValid filters are: {' '.join(__class__.__RESAMPLING_FILTERS.keys())}")

        if filter == "rerender":
            return list(self.__im(size=size, margin=margin, area=area, renderer=renderer) for size in sizes)
        else:
            img = self.__im(size=self.__max_size(sizes), margin=margin, area=area, renderer=renderer)
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
        Render the SVG as PIL.Image instance. The default rendering size is one the one provided by the SVG file.

        Args:
            dpi (int | List[int], optional): The DPI(s) to render the image(s) at.
            size (List[Union[int, Tuple[int, int]]], optional): The size(s) to render the image(s) at. 
            Can be a single integer (defining the width) or a pair for width and height. Defaults to None.
            margin (int, optional): Margin of the images (shared across all). Defaults to None.
            area (str, optional): The area to render. Valid values are 'page', 'drawing', and a string of form 'x y w h'. Defaults to 'page'.
            filter (str, optional): Which filter to use for to downscale. Use 'rerender' to render each image individual at desired size. Defaults to 'lanczos'.

        Returns:
            Union[Image.Image, List[Image.Image]]: _description_
        """
        if isinstance(dpi, int):
            dpi = [dpi]
        if isinstance(size, int):
            size = [size]

        size = self.__calc_sizes(dpi, size)

        if len(size) > 1:
            return self.__im_multi(size, margin, area, filter, renderer=renderer)
        else:
            return self.__im(size[0], margin, area, renderer=renderer)

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

    def export(self, stem: str = None, format: Union[str, List[str]] = "png", dpi: Union[int, List[int]] = None, size: List[Union[int, Tuple[int, int]]] = None, margin: int = None, area: str = 'page', filter: str = "lanczos", renderer: str = "skia"):
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
    def IM(cls, fp: Union[str, Path, bytes], dpi: Union[int, List[int]] = None, size: Union[int, Tuple[int, int]] = None, margin: int = None, area: str = 'page', renderer: str = 'skia'):
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
    def EXPORT(cls, fp: Union[str, Path, bytes], stem: str = None, format: Union[str, List[str]] = "png", dpi: Union[int, List[int]] = None, size: Union[int, Tuple[int, int]] = None, margin: int = None, area: str = 'page', filter="lanczos", renderer: str = "skia"):
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
