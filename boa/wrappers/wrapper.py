"""
########################
Base Wrapper
########################

"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from ax.core.base_trial import BaseTrial

from boa.metaclasses import WrapperRegister
from boa.wrappers.wrapper_utils import (
    load_jsonlike,
    make_experiment_dir,
    normalize_config,
)

logger = logging.getLogger(__name__)


class BaseWrapper(metaclass=WrapperRegister):
    def __init__(self, config_path: os.PathLike = None, *args, **kwargs):
        self.model_settings = {}
        self.ex_settings = {}
        self.experiment_dir = None

        if config_path:
            self.config = None
            config = self.load_config(config_path, *args, **kwargs)
            # if load_config returns something, set to self.config
            # if users overwrite load_config and don't return anything, we don't
            # want to set it to self.config if they set it in load_config
            if config is not None:
                self.config = config
            self.mk_experiment_dir(*args, **kwargs)

    def load_config(self, config_path: os.PathLike | str, *args, **kwargs) -> dict:
        """
        Load config file and return a dictionary # TODO finish this

        Parameters
        ----------
        config_path
            File path for the experiment configuration file

        Returns
        -------
        dict
            loaded_config
        """
        try:
            config = load_jsonlike(config_path, normalize=False)
        except ValueError as e:  # return empty config if not json or yaml file
            logger.warning(repr(e))
            return {}
        parameter_keys = config.get("optimization_options", {}).get("parameter_keys", None)
        config = normalize_config(config=config, parameter_keys=parameter_keys)

        self.config = config
        self.ex_settings = self.config["optimization_options"]
        self.model_settings = self.config.get("model_options", {})
        return self.config

    def mk_experiment_dir(
        self,
        experiment_dir: os.PathLike | str = None,
        working_dir: os.PathLike | str = None,
        experiment_name: str = None,
        append_timestamp: bool = True,
        **kwargs,
    ) -> None:
        """
        Make the experiment directory that boa will write all of its trials and logs to.

        Parameters
        ----------
        experiment_dir
            Path to the directory for the output of the experiment
            You may specify this or working_dir in your configuration file instead.
            (Defaults to None and using your configuration file instead)
        working_dir
            Working directory of project, experiment_dir will be placed inside
            working dir based on experiment name.
            Because of this only either experiment_dir or working_dir may be specified.
            You may specify this or experiment_dir in your configuration file instead.
            (Defaults to None and using your configuration file instead)
        experiment_name
            Name of experiment, used for creating path to experiment dir with the working dir
            (Defaults to None and using your configuration file instead)
        append_timestamp
            Whether to append a timestamp to the end of the experiment directory
            to ensure uniqueness
        """
        # grab exp dir from config file or if passed in
        experiment_dir = experiment_dir or self.ex_settings.get("experiment_dir")
        working_dir = working_dir or self.ex_settings.get("working_dir")
        experiment_name = experiment_name or self.ex_settings.get("experiment", {}).get("name", "boa_runs")
        if experiment_dir:
            mk_exp_dir_kw = dict(experiment_dir=experiment_dir, append_timestamp=append_timestamp)
        else:  # if no exp dir, instead grab working dir from config or passed in
            if not working_dir:
                # if no working dir (or exp dir) set to cwd
                working_dir = Path.cwd()

            mk_exp_dir_kw = dict(
                working_dir=working_dir, experiment_name=experiment_name, append_timestamp=append_timestamp
            )

            # We use str() because make_experiment_dir returns a Path object (json serialization)
            self.ex_settings["working_dir"] = str(working_dir)

        experiment_dir = make_experiment_dir(**mk_exp_dir_kw)
        self.ex_settings["experiment_dir"] = str(experiment_dir)
        self.experiment_dir = experiment_dir

    def write_configs(self, trial: BaseTrial) -> None:
        """
        This function is usually used to write out the configurations files used
        in an individual optimization trial run, or to dynamically write a run
        script to start an optimization trial run.

        Parameters
        ----------
        trial
        """

    def run_model(self, trial: BaseTrial) -> None:
        """
        Runs a model by deploying a given trial.

        Parameters
        ----------
        trial
        """

    def set_trial_status(self, trial: BaseTrial) -> None:
        """
        Marks the status of a trial to reflect the status of the model run for the trial.

        Each trial will be polled periodically to determine its status (completed, failed, still running,
        etc). This function defines the criteria for determining the status of the model run for a trial (e.g., whether
        the model run is completed/still running, failed, etc). The trial status is updated accordingly when the trial
        is polled.

        The approach for determining the trial status will depend on the structure of the particular model and its
        outputs. One example is checking the log files of the model.

        .. todo::
            Add examples/links of different approaches

        Parameters
        ----------
        trial : BaseTrial

        Examples
        --------
        trial.mark_completed()
        trial.mark_failed()
        trial.mark_abandoned()
        trial.mark_early_stopped()

        See Also
        --------
        # TODO add sphinx link to ax trial status
        """

    def fetch_trial_data(self, trial: BaseTrial, metric_properties: dict, metric_name: str, *args, **kwargs) -> dict:
        """
        Retrieves the trial data and prepares it for the metric(s) used in the objective
        function.

        For example, for a case where you are minimizing the error between a model and observations, using RMSE as a
        metric, this function would load the model output and the corresponding observation data that will be passed to
        the RMSE metric.

        The return value of this function is a dictionary, with keys that match the keys
        of the metric used in the objective function.
        # TODO work on this description

        Parameters
        ----------
        trial
        metric_properties
        metric_name

        Returns
        -------
        dict
            A dictionary with the keys matching the keys of the metric function
            used in the objective
        """
