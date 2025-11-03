"""
API endpoints for persona management.

Provides endpoints for:
- Loading persona cards from files
- Listing available personas
- Getting persona details
- Validating persona data
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Path as PathParam
from fastapi.responses import JSONResponse, FileResponse
import logging

from ..services.persona_reader import persona_reader
from ..models.persona import LoadedPersona, PersonaLoadError, PersonaValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("/", response_model=List[Dict[str, Any]])
async def list_personas(
    directory: Optional[str] = Query(None, description="Directory to search for personas"),
    summary_only: bool = Query(True, description="Return summary info only")
):
    """
    List all available persona cards.

    Args:
        directory: Optional directory path to search (defaults to data/personas)
        summary_only: If True, returns only summary information

    Returns:
        List of persona summaries or full persona data
    """
    try:
        # Default to the standard personas directory
        if directory is None:
            directory = "/data/personas"

        # Convert to absolute path
        directory_path = Path(directory).resolve()

        if not directory_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Directory not found: {directory}"
            )

        # Load all personas from directory
        personas = persona_reader.load_personas_from_directory(str(directory_path))

        if summary_only:
            return [persona_reader.get_persona_summary(persona) for persona in personas]
        else:
            return [persona.dict() for persona in personas]

    except PersonaLoadError as e:
        logger.error(f"Error loading personas from {directory}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error listing personas: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/load", response_model=Dict[str, Any])
async def load_persona(
    file_path: str = Query(..., description="Path to persona PNG file"),
    summary_only: bool = Query(True, description="Return summary info only")
):
    """
    Load a specific persona card from file.

    Args:
        file_path: Path to the PNG persona card file
        summary_only: If True, returns only summary information

    Returns:
        Loaded persona data or summary
    """
    try:
        # Resolve file path
        path = Path(file_path).resolve()

        # Load the persona
        persona = persona_reader.load_persona_from_file(str(path))

        if summary_only:
            return persona_reader.get_persona_summary(persona)
        else:
            return persona.dict()

    except PersonaLoadError as e:
        logger.error(f"Error loading persona from {file_path}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except PersonaValidationError as e:
        logger.error(f"Validation error for persona {file_path}: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    except Exception as e:
        logger.error(f"Unexpected error loading persona: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/test", response_model=List[Dict[str, Any]])
async def load_test_personas(summary_only: bool = Query(True, description="Return summary info only")):
    """
    Load test personas from the test directory.

    Args:
        summary_only: If True, returns only summary information

    Returns:
        List of test persona summaries or full data
    """
    try:
        test_directory = Path("/data/personas/test").resolve()

        if not test_directory.exists():
            raise HTTPException(
                status_code=404,
                detail="Test personas directory not found: data/personas/test"
            )

        # Load test personas
        personas = persona_reader.load_personas_from_directory(str(test_directory))

        if not personas:
            return []

        if summary_only:
            return [persona_reader.get_persona_summary(persona) for persona in personas]
        else:
            return [persona.dict() for persona in personas]

    except PersonaLoadError as e:
        logger.error(f"Error loading test personas: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error loading test personas: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{persona_name}", response_model=Dict[str, Any])
async def get_persona_by_name(
    persona_name: str = PathParam(..., description="Name of the persona to retrieve"),
    directory: Optional[str] = Query(None, description="Directory to search for personas"),
    summary_only: bool = Query(True, description="Return summary info only")
):
    """
    Get a specific persona by name.

    Args:
        persona_name: Name of the character to find
        directory: Optional directory path to search (defaults to data/personas)
        summary_only: If True, returns only summary information

    Returns:
        Persona data matching the name
    """
    try:
        # Default to the standard personas directory
        if directory is None:
            directory = "/data/personas"

        directory_path = Path(directory).resolve()

        if not directory_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Directory not found: {directory}"
            )

        # Load all personas and find matching name
        personas = persona_reader.load_personas_from_directory(str(directory_path))

        matching_persona = None
        for persona in personas:
            if persona.name.lower() == persona_name.lower():
                matching_persona = persona
                break

        if not matching_persona:
            raise HTTPException(
                status_code=404,
                detail=f"Persona not found: {persona_name}"
            )

        if summary_only:
            return persona_reader.get_persona_summary(matching_persona)
        else:
            return matching_persona.dict()

    except HTTPException:
        raise
    except PersonaLoadError as e:
        logger.error(f"Error loading personas: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error finding persona: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/validate")
async def validate_persona_data(persona_data: Dict[str, Any]):
    """
    Validate persona data without loading from file.

    Args:
        persona_data: Raw persona data to validate

    Returns:
        Validation result
    """
    try:
        # Validate the persona data
        persona_card = persona_reader.validate_persona_data(persona_data)

        return {
            "valid": True,
            "character_name": persona_card.data.name,
            "spec": persona_card.spec,
            "spec_version": persona_card.spec_version,
            "has_lorebook": persona_card.data.character_book is not None,
            "message": "Persona data is valid"
        }

    except PersonaValidationError as e:
        return JSONResponse(
            status_code=422,
            content={
                "valid": False,
                "error": str(e),
                "message": "Persona data validation failed"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error validating persona: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{persona_name}/image")
async def get_persona_image(
    persona_name: str = PathParam(..., description="Name of the persona to get image for"),
    expression: str = Query("default", description="Expression to display"),
    directory: Optional[str] = Query(None, description="Directory to search for personas")
):
    """
    Get the PNG image file for a specific persona with optional expression.

    Args:
        persona_name: Name of the character to find
        expression: Expression to display (default: "default")
        directory: Optional directory path to search (defaults to data/personas)

    Returns:
        PNG image file
    """
    try:
        # Default to the standard personas directory
        if directory is None:
            directory = "/data/personas"

        directory_path = Path(directory).resolve()

        if not directory_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Directory not found: {directory}"
            )

        # Find the persona
        personas = persona_reader.load_personas_from_directory(str(directory_path))

        matching_persona = None
        for persona in personas:
            if persona.name.lower() == persona_name.lower():
                matching_persona = persona
                break

        if not matching_persona:
            raise HTTPException(
                status_code=404,
                detail=f"Persona not found: {persona_name}"
            )

        # Get the requested expression or fallback to default
        expressions = matching_persona.persona.data.expressions
        if expression in expressions:
            image_path = expressions[expression]
        elif "default" in expressions:
            image_path = expressions["default"]
        else:
            # Ultimate fallback to main persona file
            image_path = matching_persona.metadata.file_path

        if not Path(image_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"Expression image not found: {expression}"
            )

        return FileResponse(
            path=image_path,
            media_type="image/png",
            filename=f"{persona_name}_{expression}.png"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error serving persona image: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{persona_name}/expressions")
async def get_persona_expressions(
    persona_name: str = PathParam(..., description="Name of the persona"),
    directory: Optional[str] = Query(None, description="Directory to search for personas")
):
    """
    Get available expressions for a persona.

    Args:
        persona_name: Name of the character
        directory: Optional directory path to search

    Returns:
        Available expressions and URLs
    """
    try:
        # Default to the standard personas directory
        if directory is None:
            directory = "/data/personas"

        directory_path = Path(directory).resolve()

        if not directory_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Directory not found: {directory}"
            )

        # Find the persona
        personas = persona_reader.load_personas_from_directory(str(directory_path))

        matching_persona = None
        for persona in personas:
            if persona.name.lower() == persona_name.lower():
                matching_persona = persona
                break

        if not matching_persona:
            raise HTTPException(
                status_code=404,
                detail=f"Persona not found: {persona_name}"
            )

        expressions = matching_persona.persona.data.expressions
        current_expression = matching_persona.persona.data.current_expression

        return {
            "persona_name": persona_name,
            "current_expression": current_expression,
            "available_expressions": list(expressions.keys()),
            "expressions": {
                name: f"/personas/{persona_name}/image?expression={name}"
                for name in expressions.keys()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting persona expressions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get expressions")


@router.post("/{persona_name}/expression")
async def set_persona_expression(
    expression_data: Dict[str, str],
    persona_name: str = PathParam(..., description="Name of the persona"),
    directory: Optional[str] = Query(None, description="Directory to search for personas")
):
    """
    Set the current expression for a persona.

    Args:
        persona_name: Name of the character
        expression_data: Dictionary containing "expression" key
        directory: Optional directory path to search

    Returns:
        Updated expression info
    """
    try:
        expression = expression_data.get("expression")
        if not expression:
            raise HTTPException(status_code=400, detail="Expression is required")

        # Default to the standard personas directory
        if directory is None:
            directory = "/data/personas"

        directory_path = Path(directory).resolve()

        if not directory_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Directory not found: {directory}"
            )

        # Find the persona
        personas = persona_reader.load_personas_from_directory(str(directory_path))

        matching_persona = None
        for persona in personas:
            if persona.name.lower() == persona_name.lower():
                matching_persona = persona
                break

        if not matching_persona:
            raise HTTPException(
                status_code=404,
                detail=f"Persona not found: {persona_name}"
            )

        expressions = matching_persona.persona.data.expressions
        if expression not in expressions:
            raise HTTPException(
                status_code=400,
                detail=f"Expression '{expression}' not available. Available: {list(expressions.keys())}"
            )

        # Update current expression
        matching_persona.persona.data.current_expression = expression

        return {
            "persona_name": persona_name,
            "expression": expression,
            "image_url": f"/personas/{persona_name}/image?expression={expression}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting persona expression: {e}")
        raise HTTPException(status_code=500, detail="Failed to set expression")