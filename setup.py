from distutils.core import setup

import hexgrid

with open("README.md", "r") as fp:
    long_description = fp.read()

setup(name="hexgrid",
      version=hexgrid.__version__,
      author="Ross Anderson",
      author_email="ross.anderson@ualberta.ca",
      url="https://github.com/rosshamish/hexgrid/",
      download_url = 'https://github.com/rosshamish/hexgrid/tarball/' + hexgrid.__version__,
      description="functions for working with a hexagonal settlers of catan grid",
      long_description=long_description,
      keywords=[],
      classifiers=[],
      license="GPLv3",

      py_modules=["hexgrid"],
	)

