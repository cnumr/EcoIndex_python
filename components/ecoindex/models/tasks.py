from typing import Any

from ecoindex.models import Result
from pydantic import AnyHttpUrl, BaseModel, Field


class QueueTaskError(BaseModel):
    detail: Any | None = Field(
        default=None, title="Detail object of the raised exception"
    )
    exception: str = Field(default=..., title="Name of the exception that was raised")
    message: str = Field(default=..., title="Message of the exception")
    status_code: int | None = Field(
        default=None, title="Corresponding original HTTP status code sended by the API"
    )
    url: AnyHttpUrl | None = Field(default=None, title="URL of the analyzed web page")


class QueueTaskResult(BaseModel):
    status: str | None = Field(
        default=None,
        title="Status of the ecoindex analysis.",
        description=(
            "While the task is pending or the analysis is running, it is null."
            " But once the analysis is complete, it should return SUCCESS or FAILURE."
        ),
    )
    detail: Result | None = Field(
        default=None,
        title="Result of the ecoindex analysis once it was successfuly completed",
    )
    error: QueueTaskError | None = Field(
        default=None, title="Detail of the ecoindex error if it is not successful"
    )


class QueueTaskApi(BaseModel):
    id: str = Field(
        default=...,
        title=(
            "Identifier of the current. "
            "This identifier will become the identifier of the analysis"
        ),
    )
    status: str = Field(
        default=...,
        title="Status of the current task. Can be PENDING, FAILURE, SUCCESS",
    )
    queue_position: int | None = Field(
        default=None,
        title="Position of the task in the waiting queue (0 = next to run)",
        description="Null when the task is running or already completed.",
    )
    tasks_in_progress: int = Field(
        default=0,
        title="Number of tasks currently being processed on this queue",
    )
    ecoindex_result: QueueTaskResult | None = Field(
        default=None, title="Result of the Ecoindex analysis"
    )
    task_error: Any | None = Field(
        default=None,
        title="Detail of the error encountered by the task in case of Failure",
    )


class QueueTaskApiBatch(BaseModel):
    id: str = Field(
        default=...,
        title=(
            "Identifier of the current. "
            "This identifier will become the identifier of the analysis"
        ),
    )
    status: str = Field(
        default=...,
        title="Status of the current task. Can be PENDING, FAILURE, SUCCESS",
    )
    task_error: Any | None = Field(
        default=None,
        title="Detail of the error encountered by the task in case of Failure",
    )
