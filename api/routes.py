from fastapi import APIRouter, Request, Response, status
from pydantic import ValidationError

from .depends import Cursor, EmbeddedEvent, IdPath, Session
from .exc import ClientError, InternalError
from .logger import Logger
from .schemas import CursorResponse, ErrorResponse, EventFullSchema, ResponsePage
from .services import get_event, get_events, save_event

v1_router = APIRouter(prefix="/v1.0", tags=["v1"], redirect_slashes=True)


@v1_router.get(
    "/events",
    tags=["read"],
    # status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ResponsePage[EventFullSchema],
            "description": "Invalid query parameters",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Invalid query parameters",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal error, try again later",
        },
    },
    response_model_exclude_none=True,
)
def read_events(response: Response, cursor: Cursor, session: Session):
    if isinstance(cursor.next_, str):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ErrorResponse(detail=cursor.next_)
    page = ResponsePage.model_validate({"data": [], "paging": cursor})
    try:
        raw_page, _new_cursor = get_events(session, cursor)
        page.data = [
            EventFullSchema.model_validate(raw_event, from_attributes=True, by_name=True)
            for raw_event in raw_page
        ]
        page.paging = CursorResponse.model_validate(_new_cursor, by_name=True)
    except InternalError as e_internal:
        Logger.error(
            "Internal error retrieving page of size %r. (Type=%s,Msg=%s)",
            cursor,
            type(e_internal.internal_exc).__name__,
            e_internal.msg,
        )
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return page


@v1_router.get(
    "/events/{id}",
    tags=["read"],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": EventFullSchema,
            "description": "Single event requested by id",
        },
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Event not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
    response_model_exclude_none=True,
)
def find_event(response: Response, cursor: IdPath, session: Session):
    print("This is cursor", cursor)
    if cursor is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ErrorResponse(detail="Event id is not a valid id")
    try:
        model = get_event(session, cursor)
        if model is None:
            raise InternalError(f"Cannot found event with id {cursor}", None)
        model_dict = model._asdict()
        schema = EventFullSchema.model_validate(model_dict, by_name=True)
        return schema
    except (ValidationError, InternalError) as e_internal:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        session.rollback()
        type_error = (
            "ValidationError"
            if isinstance(e_internal, ValidationError)
            else type(e_internal.internal_exc).__name__
        )
        Logger.error(
            "Internal error finding event with id %s. (Type=%s,Msg=%s)",
            cursor,
            type_error,
            e_internal.title if isinstance(e_internal, ValidationError) else e_internal.msg,
        )
        return ErrorResponse(detail="Unable to find record, Internal server error")
    except ClientError as e_cli:
        response.status_code = status.HTTP_400_BAD_REQUEST
        session.rollback()
        return ErrorResponse(detail=f"Server: {e_cli.msg}")


@v1_router.post(
    "/events",
    tags=["create"],
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "New event stored", "model": EventFullSchema},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error",
            "model": ErrorResponse,
        },
        status.HTTP_400_BAD_REQUEST: {"description": "Client side error", "model": ErrorResponse},
    },
    response_model_exclude_none=True,
)
def add_event(req: Request, response: Response, session: Session, event: EmbeddedEvent):
    try:
        model = save_event(session, event)
        if model is None:
            session.rollback()
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return ErrorResponse(detail="Internal error, cannot process request")
        model_dict = model._asdict()
        schema = EventFullSchema.model_validate(model_dict, by_name=True)
        return schema
    except (InternalError, ValidationError) as e_internal:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        type_error = (
            "ValidationError"
            if isinstance(e_internal, ValidationError)
            else type(e_internal.internal_exc).__name__
        )
        Logger.error(
            "Internal error creating new event. (Type=%s,Msg=%s)",
            type_error,
            str(e_internal) if isinstance(e_internal, ValidationError) else e_internal.msg,
        )
        return ErrorResponse(detail="Unable to process event, internal server error")
    except ClientError as e_cli:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ErrorResponse(detail=f"Server: {e_cli.msg}")
