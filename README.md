# eWaterCycle plugin for HYPE hydrological model

[![Research Software Directory Badge](https://img.shields.io/badge/rsd-00a3e3.svg)](https://www.research-software.nl/software/ewatercycle-hype)

HYPE plugin for [eWatercycle](https://ewatercycle.readthedocs.io/).

HYPE documentation at http://www.smhi.net/hype/wiki/doku.php .

## Installation

eWaterCycle must be installed in a [mamba](https://conda-forge.org/miniforge/) environment. The environment can be created with

```console
wget https://raw.githubusercontent.com/eWaterCycle/ewatercycle/main/environment.yml
mamba env create --name ewatercycle-hype --file environment.yml
conda activate ewatercycle-hype
```

Install this package alongside your eWaterCycle installation

```console
pip install ewatercycle-hype
```

Then Hype becomes available as one of the eWaterCycle models

```python
from ewatercycle.models import Hype
```

## Usage

Usage of HYPE forcing generation and model execution is shown in 
[docs/generate_forcing.ipynb](https://github.com/eWaterCycle/ewatercycle-hype/tree/main/docs/generate_forcing.ipynb) and [docs/model.ipynb](https://github.com/eWaterCycle/ewatercycle-hype/tree/main/docs/model.ipynb) respectively.

## License

`ewatercycle-hype` is distributed under the terms of the [Apache-2.0](https://spdx.org/licenses/Apache-2.0.html) license.
