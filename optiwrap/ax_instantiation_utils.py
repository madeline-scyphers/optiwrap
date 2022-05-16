from __future__ import annotations

import time

from ax import Experiment, Objective, OptimizationConfig, Runner, SearchSpace
from ax.modelbridge.dispatch_utils import choose_generation_strategy
from ax.modelbridge.generation_strategy import GenerationStrategy
from ax.service.ax_client import AxClient
from ax.service.scheduler import Scheduler, SchedulerOptions
from ax.service.ax_client import AxClient
# from ax.storage.sqa_store.structs import DBSettings
# from ax.storage.sqa_store.db import create_all_tables, get_engine, init_engine_and_session_factory
# from ax.storage.sqa_store.decoder import Decoder
# from ax.storage.sqa_store.encoder import Encoder
# from ax.storage.sqa_store.sqa_config import SQAConfig

from optiwrap.metrics.metrics import get_metric_from_config
from optiwrap.utils import get_dictionary_from_callable


def instantiate_search_space_from_json(
    parameters: list | None = None, parameter_constraints: list | None = None
) -> SearchSpace:
    parameters = parameters if parameters is not None else []
    parameter_constraints = parameter_constraints if parameter_constraints is not None else []
    return AxClient.make_search_space(parameters, parameter_constraints)


def generation_strategy_from_experiment(experiment: Experiment, config: dict) -> GenerationStrategy:
    return choose_generation_strategy(
        search_space=experiment.search_space,
        **get_dictionary_from_callable(choose_generation_strategy, config),
    )


def get_scheduler(
    experiment: Experiment,
    generation_strategy: GenerationStrategy = None,
    scheduler_options: SchedulerOptions = None,
    config: dict = None,
):
    scheduler_options = scheduler_options or SchedulerOptions(
        **config["optimization_options"]["scheduler"]
    )
    if generation_strategy is None:
        if (
            "total_trials" in config["optimization_options"]["scheduler"]
            and "num_trials" not in config["optimization_options"]["generation_strategy"]
        ):
            config["optimization_options"]["generation_strategy"]["num_trials"] = config[
                "optimization_options"
            ]["scheduler"]["total_trials"]
        generation_strategy = generation_strategy_from_experiment(
            experiment, config["optimization_options"]["generation_strategy"]
        )
    # db_settings = DBSettings(
    #     url="sqlite:///foo.db",
    #     decoder=Decoder(config=SQAConfig()),
    #     encoder=Encoder(config=SQAConfig()),
    # )

    # init_engine_and_session_factory(url=db_settings.url)
    # engine = get_engine()
    # create_all_tables(engine)

    return Scheduler(
        experiment=experiment,
        generation_strategy=generation_strategy,
        options=scheduler_options,
        # db_settings=db_settings,
    )


def get_experiment(
    config: dict,
    runner: Runner,
    wrapper=None,
):
    settings = config["optimization_options"]

    search_space = instantiate_search_space_from_json(
        config.get("search_space_parameters"), config.get("search_space_parameter_constraints")
    )

    metric = get_metric_from_config(settings["metric"], wrapper=wrapper, param_names=list(search_space.parameters))
    objective = Objective(metric=metric, minimize=True)

    if "name" not in settings["experiment"]:
        if "name" in settings:
            settings["experiment"]["name"] = settings["name"]
        else:
            settings["experiment"]["name"] = time.time()

    return Experiment(
        search_space=search_space,
        optimization_config=OptimizationConfig(objective=objective),
        runner=runner,
        **get_dictionary_from_callable(Experiment.__init__, settings["experiment"]),
    )
