<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]
[![Python][Python-badge]][Python-url]




<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/jlwoolf/pillow-svg">
    <img src="https://raw.githubusercontent.com/jlwoolf/pillow-svg/master/logo.svg" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">Pillow-SVG</h3>

  <p align="center">
    A python library to make working with SVG files easier.
    <br />
    <a href="https://github.com/jlwoolf/pillow-svg"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/jlwoolf/pillow-svg/issues">Report Bug</a>
    ·
    <a href="https://github.com/jlwoolf/pillow-svg/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#installation">Installation</a>
      <ul>
        <li><a href="#inkscape">Inkscape</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

<!-- [![Product Name Screen Shot][product-screenshot]](https://example.com) -->

Pillow-SVG is a python image library with the goal of adding some form of svg integration to pillow. Currently the library works by using a rendering engine to create a rasterized image at a desired resolution, returned as an instance of PIL.Image. Only two renderers, [inkscape](https://inkscape.org/) and [skia](https://skia.org/) are supported as of now. There is also a command-line utility that is a little more limited, but makes converting large quantities of svg's easy.



<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Installation

While I quite like the name pillow-svg, the name is currently in use by another library on PyPi. I'm currently talking with the owner of that library to work on merging their functionality with my own, but for now Pillow-SVG requires manual build and install. To install Pillow-SVG, please build the package and install the wheel.

```
python3 -m build
python3 -m pip install --upgrade pip
python3 -m pip install ./dist/pillow_svg-1.0.3-py3-none-any.whl
```

### Skia

The default render used is Skia, which is installed alongside Pillow-SVG with pip.  You can read more about it [here](https://skia.org/docs/). It should be enough for most cases, however, I have personally had issues when trying to render Inkscape SVG files. If you do encounter problems, I would recommend the Inkscape renderer, although it is slower.

### Inkscape

Pillow-SVG does not require inkscape to work, but if you would like to use the inkscape renderer, please install inkscape from [here](https://inkscape.org/release/inkscape-1.2.1/) and make sure it has been added to the PATH.



<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage

Load svg file as SVG instance
```py
from pillow_svg import SVG

svg = SVG('path/to/svg/file.svg')
```

Create PIL.Image instance from the svg
```py
from pillow_svg import SVG

svg = SVG('path/to/svg/file.svg')
img = svg.im()
```

You can specify the dpi of the rendered image or the size in pixels.

```py
from pillow_svg import SVG

svg = SVG('path/to/svg/file.svg')
img = svg.im(dpi=32) # img has DPI of 32
img = svg.im(size=100) # img resolution of width 100px and proportional height
img = svg.im(size=(100,150)) # img resolution of (100px, 150px)
```

You can also create multiple images of varying resolutions at once.
```py
from pillow_svg import SVG

svg = SVG('path/to/svg/file.svg')
images = svg.im(dpi=[32, 48, 96], size=[(1200, 1400), 120, (80, 50)]) 
```

By default, when create multiple images, the highest specified resolution is rendered, with all others downscaled from it. The downscaling filter used
can be specified, with the filters being defined by [pillow](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Resampling). If the filter
is set to `rerender` then each image is rendered individual at the specified resolution (this will be slower).

```py
from pillow_svg import SVG

svg = SVG('path/to/svg/file.svg')
images = svg.im(dpi=[32, 48, 96], size=[(1200, 1400), 120, (80, 50)], filter='nearest') # faster
images = svg.im(dpi=[32, 48, 96], size=[(1200, 1400), 120, (80, 50)], filter='rerender') # slower 
```

You can also directly export the svg's to any supported [pillow image format](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html).
```py
from pillow_svg import SVG

svg = SVG('path/to/svg/file.svg')
# creates file ./path/to/svg/file.png
img = svg.export(format="png")
```

All arguments that are used by `SVG::im` can also be called with `SVG::export`. You can specify which formats using the `format` argument, and the output file name/location using the `stem` argument. Specifying multiple DPI's and sizes will create multiple exports named based off their resolution.

```py
from pillow_svg import SVG

svg = SVG('path/to/svg/file.svg')

# creates two files: 
#   ./out/file.png 
#   ./out/file.jpeg
img = svg.export(stem='out/file', format=['png','jpeg'], dpi=48)

# creates four files: 
#   ./out/file2_100_80.png
#   ./out/file2_200_150.png
#   ./out/file2_100_80.jpeg
#   ./out/file2_200_150.jpg
img = svg.export(stem='out/file2', format=['png','jpeg'], size=[(100, 80), (200, 150)])
```

Finally, if you do not need to create an SVG instance, there are class method variations of both `SVG::im` and `SVG::export` which take the filepath directly, loading an Image instance or exporting.
```py
from pillow_svg import SVG

img = SVG.IM('path/to/svg/file.svg')
SVG.EXPORT('path/to/svg/file.svg')
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

I made this library for myself, so its functionality is really limited to my own personal applications. So if you have any contributions to help make this library even better, that would be **greatly appreciated**. I had plans to make a GUI interface, and implement some basic tests, but just haven't gotten around to it, so if you have some spare time and are interested in fleshing this library out more, go right on ahead.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/NewFeature`)
3. Commit your Changes (`git commit -m 'Added some New Feature'`)
4. Push to the Branch (`git push origin feature/NewFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Jonathan Woolf  - jlwoolf@proton.me

Project Link: [https://github.com/jlwoolf/pillow-svg](https://github.com/jlwoolf/pillow-svg)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/jlwoolf/pillow-svg.svg?style=for-the-badge
[contributors-url]: https://github.com/jlwoolf/pillow-svg/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/jlwoolf/pillow-svg.svg?style=for-the-badge
[forks-url]: https://github.com/jlwoolf/pillow-svg/network/members
[stars-shield]: https://img.shields.io/github/stars/jlwoolf/pillow-svg.svg?style=for-the-badge
[stars-url]: https://github.com/jlwoolf/pillow-svg/stargazers
[issues-shield]: https://img.shields.io/github/issues/jlwoolf/pillow-svg.svg?style=for-the-badge
[issues-url]: https://github.com/jlwoolf/pillow-svg/issues
[license-shield]: https://img.shields.io/github/license/jlwoolf/pillow-svg.svg?style=for-the-badge
[license-url]: https://github.com/jlwoolf/pillow-svg/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/jlwoolf
[product-screenshot]: images/screenshot.png
[Python-badge]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/