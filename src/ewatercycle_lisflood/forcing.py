"""Forcing related functionality for lisflood."""

import logging
from pathlib import Path
from typing import Optional, cast

from ewatercycle.base.forcing import DefaultForcing
from ewatercycle.esmvaltool.builder import RecipeBuilder
from ewatercycle.esmvaltool.schema import Dataset, Recipe, TargetGrid
from ewatercycle_lisflood.lisvap import create_lisvap_config, lisvap
from ewatercycle.util import (
    fit_extents_to_grid,
    get_extents,
    get_time,
    reindex,
    to_absolute_path,
)

logger = logging.getLogger(__name__)


class LisfloodForcing(DefaultForcing):
    """Container for lisflood forcing data.

    Args:
        directory: Directory where forcing data files are stored.
        start_time: Start time of forcing in UTC and ISO format string e.g.
            'YYYY-MM-DDTHH:MM:SSZ'.
        end_time: End time of forcing in UTC and ISO format string e.g.
            'YYYY-MM-DDTHH:MM:SSZ'.
        shape: Path to a shape file. Used for spatial selection.
        PrefixPrecipitation: Path to a NetCDF or pcraster file with
            precipitation data
        PrefixTavg: Path to a NetCDF or pcraster file with average
            temperature data
        PrefixE0: Path to a NetCDF or pcraster file with potential
            evaporation rate from open water surface data
        PrefixES0: Path to a NetCDF or pcraster file with potential
            evaporation rate from bare soil surface data
        PrefixET0: Path to a NetCDF or pcraster file with potential
            (reference) evapotranspiration rate data

    Example:

    To load forcing data from a directory:

        .. code-block:: python

            from ewatercycle.forcing import sources

            forcing = sources.LisfloodForcing(
                directory='/data/lisflood-forcings-case1',
                start_time='1989-01-02T00:00:00Z',
                end_time='1999-01-02T00:00:00Z',
                PrefixPrecipitation='tp.nc',
                PrefixTavg='ta.nc',
                PrefixE0='e.nc',
                PrefixES0='es.nc',
                PrefixET0='et.nc'
            )
    """

    PrefixPrecipitation: str = "pr.nc"
    PrefixTavg: str = "tas.nc"
    PrefixE0: str = "e0.nc"
    PrefixES0: str = "es0.nc"
    PrefixET0: str = "et0.nc"
    # TODO check whether start/end time are same as in the files

    @classmethod
    def generate(  # type: ignore
        cls,
        dataset: Dataset | str | dict,
        start_time: str,
        end_time: str,
        shape: str,
        directory: Optional[str] = None,
        target_grid: Optional[dict] = None,
        run_lisvap: Optional[dict] = None,
    ) -> "LisfloodForcing":
        """Generate forcings for a model.

        The forcing is generated with help of
        `ESMValTool <https://esmvaltool.org/>`_.

        Args:
            dataset: Dataset to get forcing data from.
                When string is given a predefined dataset is looked up in
                :py:const:`ewatercycle.esmvaltool.datasets.DATASETS`.
                When dict given it is passed to
                :py:class:`ewatercycle.esmvaltool.models.Dataset` constructor.
            start_time: Start time of forcing in UTC and ISO format string e.g.
                'YYYY-MM-DDTHH:MM:SSZ'.
            end_time: nd time of forcing in UTC and ISO format string e.g.
                'YYYY-MM-DDTHH:MM:SSZ'.
            shape: Path to a shape file. Used for spatial selection.
            directory:  Directory in which forcing should be written.
                If not given will create timestamped directory.
            target_grid: the ``target_grid`` should be a ``dict`` with the
                following keys:

                - ``start_longitude``: longitude at the center of the first grid cell.
                - ``end_longitude``: longitude at the center of the last grid cell.
                - ``step_longitude``: constant longitude distance between grid cell \
                    centers.
                - ``start_latitude``: latitude at the center of the first grid cell.
                - ``end_latitude``: longitude at the center of the last grid cell.
                - ``step_latitude``: constant latitude distance between grid cell \
                    centers.

                Make sure the target grid matches up with the grid in the mask_map
                and files in parameterset_dir.
                Also the `shape` should be within the target grid.

                If not given will guestimate target grid from `shape`
                using a 0.1x0.1 grid with 0.05 offset.
            run_lisvap: Lisvap specification. Default is None.
                If lisvap should be run then
                give a dictionary with following key/value pairs:

                    - lisvap_config: Name of Lisvap configuration file.
                    - mask_map: A mask for the spatial selection.
                        This file should have same extent and resolution
                        as parameter-set.
                    - parameterset_dir: Directory of the parameter set.
                        Directory should contains the Lisvap config file
                        and files the config points to.
        """
        # Cannot call super as we want recipe_output not forcing object
        start_year = get_time(start_time).year
        end_year = get_time(end_time).year
        recipe = build_lisflood_recipe(
            start_year=start_year,
            end_year=end_year,
            shape=Path(shape),
            dataset=dataset,
            target_grid=target_grid,
        )
        forcing_files = cls._run_recipe(
            recipe, directory=Path(directory) if directory else None
        )
        directory = forcing_files["directory"]

        if run_lisvap:
            # Get lisvap specific options and make paths absolute
            lisvap_config = str(to_absolute_path(run_lisvap["lisvap_config"]))
            mask_map = str(to_absolute_path(run_lisvap["mask_map"]))
            parameterset_dir = str(to_absolute_path(run_lisvap["parameterset_dir"]))

            # Reindex data because recipe cropped the data
            # Also, create a sub dir for reindexed dataset because xarray does not
            # let to overwrite!
            reindexed_forcing_directory = Path(f"{directory}/reindexed")
            reindexed_forcing_directory.mkdir(parents=True, exist_ok=True)
            for var_name in {"pr", "tas", "tasmax", "tasmin", "sfcWind", "rsds", "e"}:
                reindex(
                    f"{directory}/{forcing_files[var_name]}",
                    var_name,
                    mask_map,
                    f"{reindexed_forcing_directory}/{forcing_files[var_name]}",
                )
            # Add lisvap file names
            basin = Path(shape).stem
            for var_name in {"e0", "es0", "et0"}:
                forcing_files[
                    var_name
                ] = f"lisflood_{dataset}_{basin}_{var_name}_{start_year}_{end_year}.nc"

            if isinstance(dataset, Dataset):
                lisvap_dataset = dataset.dataset
            elif isinstance(dataset, dict):
                lisvap_dataset = dataset["dataset"]
            else:
                lisvap_dataset = dataset
            config_file = create_lisvap_config(
                parameterset_dir,
                str(reindexed_forcing_directory),
                lisvap_dataset,
                lisvap_config,
                mask_map,
                start_time,
                end_time,
                forcing_files,
            )
            lisvap(
                parameterset_dir,
                str(reindexed_forcing_directory),
                mask_map,
                config_file,
            )
            # TODO add a logger message about the results of lisvap using
            # exit_code, stdout, stderr
            # Instantiate forcing object based on generated data
            generated_forcing = cls(
                directory=str(reindexed_forcing_directory),
                start_time=start_time,
                end_time=end_time,
                shape=shape,
                PrefixPrecipitation=forcing_files["pr"],
                PrefixTavg=forcing_files["tas"],
                PrefixE0=forcing_files["e0"],
                PrefixES0=forcing_files["es0"],
                PrefixET0=forcing_files["et0"],
            )
        else:
            message = (
                "Parameter `run_lisvap` is set to False. No forcing data will be "
                "generated for 'e0', 'es0' and 'et0'. However, the recipe creates "
                f"LISVAP input data that can be found in {directory}."
            )
            logger.warning("%s", message)
            # instantiate forcing object based on generated data
            generated_forcing = cls(
                directory=Path(directory),
                start_time=start_time,
                end_time=end_time,
                shape=shape,
                PrefixPrecipitation=forcing_files["pr"],
                PrefixTavg=forcing_files["tas"],
            )
        generated_forcing.save()
        return generated_forcing


def build_lisflood_recipe(
    start_year: int,
    end_year: int,
    shape: Path,
    dataset: Dataset | str | dict,
    target_grid: Optional[dict] = None,
) -> Recipe:
    """Build an ESMValTool recipe for lisflood forcing.

    Args:
        start_year: Start year of forcing.
        end_year: End year of forcing.
        shape: Path to a shape file. Used for spatial selection.
        dataset: Dataset to get forcing data from.
            When string is given a predefined dataset is looked up in
            :py:const:`ewatercycle.esmvaltool.datasets.DATASETS`.
            When dict given it is passed to
            :py:class:`ewatercycle.esmvaltool.models.Dataset` constructor.
        target_grid: the ``target_grid`` should be a ``dict`` with the
            following keys:
                start_longitude, end_longitude, start_latitude, end_latitude
    """
    if target_grid is None:
        logger.warning("target_grid was not given, guestimating from shape")
        step = 0.1
        target_grid = fit_extents_to_grid(get_extents(shape), step=step)
        target_grid.update(
            {
                "step_longitude": step,
                "step_latitude": step,
            }
        )

    return (
        RecipeBuilder()
        .title("Lisflood forcing recipe")
        .description("Lisflood forcing recipe")
        .dataset(dataset)
        .start(start_year)
        .end(end_year)
        .regrid(target_grid=cast(TargetGrid, target_grid), scheme="linear")
        .shape(shape, crop=True)
        .add_variable("pr", units="kg m-2 d-1")
        .add_variable("tas", units="degC")
        # Rest of variables are inputs for lisvap
        .add_variable("tasmin", units="degC")
        .add_variable("tasmax", units="degC")
        .add_variable("tdps", units="degC", mip="Eday")
        .add_variables(["uas", "vas"])
        .add_variable("rsds", units="J m-2 day-1")
        .script("hydrology/lisflood.py", {"catchment": shape.stem})
        .build()
    )
