from fastapi.templating import Jinja2Templates
from fastapi import Request
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "static/html_templates"))


def form_to_model(model: type):
    async def dependency(request: Request):
        form = await request.form()
        data = dict(form)

        if "interests" in data and isinstance(data["interests"], str):
            data["interests"] = [
                item.strip() for item in data["interests"].split(",") if item.strip()
            ]

        if "deleted_images" in data and isinstance(data["deleted_images"], str):
            try:
                data["deleted_images"] = (
                    data["deleted_images"].split(",") if data["deleted_images"] else []
                )
            except Exception:
                data["deleted_images"] = []

        if "images" in data and isinstance(data["images"], str):
            try:
                parsed = json.loads(data["images"])
                data["images"] = parsed if isinstance(parsed, list) else []
            except Exception:
                data["images"] = []

        request.state.form_data = data
        return model.model_validate(data)

    return dependency


def render(
    request: Request, template: str, context: dict | None = None, status_code: int = 200
):
    ctx = {"request": request, "form": {}, "errors": []}

    if context:
        ctx.update(context)

    return templates.TemplateResponse(
        name=template, context=ctx, request=request, status_code=status_code
    )
