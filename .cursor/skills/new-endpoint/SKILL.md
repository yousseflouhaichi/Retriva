# Skill: Add a new FastAPI endpoint

Use this when adding a new route to any router in backend/routers/.

## Steps
1. Define request and response Pydantic v2 models in models/schemas.py first
2. Add the async endpoint function to the appropriate router file
3. Use FastAPI Depends to inject settings and Qdrant client
4. Router function must only validate input, call a service, return output
5. Add docstring to the endpoint explaining what it does
6. Use correct HTTP status codes (202 for async jobs, 404 for missing, etc.)
7. Wrap service call in try/except, raise HTTPException with clear message

## Template
```python
@router.post("/example", response_model=ExampleResponse, status_code=202)
async def example_endpoint(
    request: ExampleRequest,
    settings: Settings = Depends(get_settings),
    qdrant: AsyncQdrantClient = Depends(get_qdrant_client),
) -> ExampleResponse:
    """
    What this endpoint does and what it returns.
    """
    try:
        result = await example_service.run(request.param, settings)
        return ExampleResponse(data=result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unexpected error occurred")
```