"""
###################################
Controller
###################################

The Controller class controls the optimization.

"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Type

from ax import Experiment
from ax.service.scheduler import Scheduler

from boa.ax_instantiation_utils import get_experiment, get_scheduler
from boa.definitions import PathLike
from boa.logger import get_formatter, get_logger
from boa.runner import WrappedJobRunner
from boa.storage import scheduler_from_json_file
from boa.wrappers.base_wrapper import BaseWrapper
from boa.wrappers.wrapper_utils import get_dt_now_as_str, initialize_wrapper


class Controller:
    """
    Controls the instantiation of your :class:`.BaseWrapper` and the
    necessary Ax objects to start your Experiment and control
    the Ax scheduler. Once the Controller sets up your Experiment, it starts
    the scheduler, which runs your trials. It then
    saves the scheduler to a json file.

    Parameters
    ----------
    config_path
        Path to configuration yaml or json file
    wrapper
        Your Wrapper subclass of BaseWrapper to be instantiated

    See Also
    --------
    :ref:`Creating a configuration File`

    """

    def __init__(
        self,
        wrapper: Type[BaseWrapper] | BaseWrapper | PathLike,
        config_path: PathLike = None,
        config: dict = None,
        **kwargs,
    ):
        if not (config or config_path or isinstance(wrapper, BaseWrapper)):
            raise TypeError("Controller __init__() requires either config_path or config or an instantiated wrapper")
        if not isinstance(wrapper, BaseWrapper):
            wrapper = self.initialize_wrapper(wrapper=wrapper, config=config, config_path=config_path, **kwargs)
        self.wrapper = wrapper
        self.config = self.wrapper.config

        self.experiment: Experiment = None
        self.scheduler: Scheduler = None
        self.logger = self.start_logger()

    @classmethod
    def from_scheduler_path(cls, scheduler_path, wrapper: BaseWrapper | Type[BaseWrapper] | PathLike = None, **kwargs):
        if wrapper:
            wrapper = cls.initialize_wrapper(wrapper, **kwargs)
            scheduler = scheduler_from_json_file(scheduler_path, wrapper=wrapper)
        else:
            scheduler = scheduler_from_json_file(scheduler_path, **kwargs)
            wrapper = scheduler.experiment.runner.wrapper
            if "config_path" in kwargs:
                config = wrapper.load_config(kwargs["config_path"])
                wrapper.config = config

        inst = cls(wrapper=wrapper, **kwargs)
        inst.scheduler = scheduler
        inst.experiment = scheduler.experiment
        return inst

    @staticmethod
    def initialize_wrapper(*args, **kwargs):
        return initialize_wrapper(*args, **kwargs)

    def start_logger(self):
        self.logger = get_logger(__name__)
        fh = logging.FileHandler(str(Path(self.wrapper.experiment_dir) / "optimization.log"))
        formatter = get_formatter()
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        return self.logger

    def initialize_scheduler(self, **kwargs) -> tuple[Scheduler, BaseWrapper]:
        """
        Sets experiment and scheduler

        Parameters
        ----------
        kwargs
            kwargs to pass to get_experiment and get_scheduler

        Returns
        -------
        returns a tuple with the first element being the scheduler
        and the second element being your wrapper (both initialized
        and ready to go)
        """

        self.experiment = get_experiment(self.config, WrappedJobRunner(wrapper=self.wrapper), self.wrapper, **kwargs)
        self.scheduler = get_scheduler(self.experiment, config=self.config, **kwargs)
        return self.scheduler, self.wrapper

    def run(self, scheduler: Scheduler = None, wrapper: BaseWrapper = None) -> Scheduler:
        """
        Run trials for scheduler

        Parameters
        ----------
        scheduler
            initialed scheduler or None, if None, defaults to
            ``self.scheduler`` (the scheduler set up in :meth:`.Controller.initialize_scheduler`
        wrapper
            initialed wrapper or None, if None, defaults to
            ``self.wrapper`` (the wrapper set up in :meth:`.Controller.initialize_wrapper`

        Returns
        -------
        The scheduler after all trials have been run or the
        experiment has been stopped for another reason.
        """
        start = time.time()
        self.logger.info("Start time: %s", get_dt_now_as_str())

        scheduler = scheduler or self.scheduler
        wrapper = wrapper or self.wrapper
        if not scheduler or not wrapper:
            raise ValueError("Scheduler and wrapper must be defined, or setup in setup method!")

        try:
            scheduler.run_all_trials()
        finally:
            self.logger.info("Trials completed! Total run time: %d", time.time() - start)
        return scheduler
