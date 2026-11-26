from fastapi import FastAPI, HTTPException

from app.schema import TicketRequest, TicketResponse
from app.triage import process_ticket
from app.logger import get_logger
from pydantic import ValidationError
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

logger = get_logger(__name__)

app = FastAPI(
    title="LLMOps Ticket Triage API",
    description="An AI-powered support ticket classification API",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "LLMOps Ticket Triage API is running"
    }


@app.get("/healthz")
def health_check():
    return {
        "status": "healthy"
    }

@app.get("/metrics")
def metrics():

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.post("/triage", response_model=TicketResponse)
def triage_ticket(request: TicketRequest):

    try:
        logger.info("Received ticket for processing")

        result = process_ticket(request.ticket)

        return result

    except RuntimeError as error:

        logger.error(f"LLM service failure: {error}")

        raise HTTPException(
            status_code=503,
            detail="LLM service is currently unavailable. Please try again later."
        )

    except ValidationError as error:

            logger.error(f"Invalid LLM response: {error}")

            raise HTTPException(
                status_code=502,
                detail="The AI service returned an invalid response. Please try again."
            )

    except Exception as error:

        logger.exception(f"Unexpected error during ticket processing: {error}")

        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the ticket."
        )
