# eWaterCycle plugin for LISFLOOD hydrological model

[![Research Software Directory Badge](https://img.shields.io/badge/rsd-00a3e3.svg)](https://www.research-software.nl/software/ewatercycle-lisflood)

LISFLOOD plugin for [eWatercycle](https://ewatercycle.readthedocs.io/).

LISFLOOD documentation at http://www.smhi.net/lisflood/wiki/doku.php .

## Installation

eWaterCycle must be installed in a [mamba](https://conda-forge.org/miniforge/) environment. The environment can be created with

```console
wget https://raw.githubusercontent.com/eWaterCycle/ewatercycle/main/environment.yml
mamba env create --name ewatercycle-lisflood --file environment.yml
conda activate ewatercycle-lisflood
```

Install this package alongside your eWaterCycle installation

```console
pip install ewatercycle-lisflood
```

Then Lisflood becomes available as one of the eWaterCycle models

```python
from ewatercycle.models import Lisflood
```

## Usage

Usage of LISFLOOD forcing generation and model execution is shown in
[docs/generate_forcing.ipynb](https://github.com/eWaterCycle/ewatercycle-lisflood/tree/main/docs/generate_forcing.ipynb) and [docs/model.ipynb](https://github.com/eWaterCycle/ewatercycle-lisflood/tree/main/docs/model.ipynb) respectively.

## License

`ewatercycle-lisflood` is distributed under the terms of the [Apache-2.0](https://spdx.org/licenses/Apache-2.0.html) license.
