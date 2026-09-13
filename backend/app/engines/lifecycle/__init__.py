"""End-to-End Project Lifecycle Orchestration V1.

Consumes frozen intelligence engines. Does not rewrite them.
"""

__all__ = [
    "get_project_lifecycle",
    "parse_lifecycle_data_mode",
    "record_planning_decision",
]


def __getattr__(name: str):
    if name in __all__:
        from app.engines.lifecycle.service import (
            get_project_lifecycle,
            parse_lifecycle_data_mode,
            record_planning_decision,
        )

        exports = {
            "get_project_lifecycle": get_project_lifecycle,
            "parse_lifecycle_data_mode": parse_lifecycle_data_mode,
            "record_planning_decision": record_planning_decision,
        }
        return exports[name]
    raise AttributeError(name)
