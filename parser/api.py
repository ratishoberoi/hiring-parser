"""FastAPI interface for the shared parser implementation."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .core import parse_brief

app = FastAPI(title="Hiring Brief Parser")


class ParseRequest(BaseModel):
    text: str


@app.post("/parse")
def parse(request: ParseRequest) -> dict:
    try:
        return {"criteria": parse_brief(request.text)}
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
