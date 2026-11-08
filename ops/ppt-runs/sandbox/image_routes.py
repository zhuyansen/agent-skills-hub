"""Model routing and request formats for the image test (ops/image-runs), used by image_proxy.py
when IMAGE_ROUTES=1. Pure functions, no network: tested by ops/image-runs/test_image_routes.py.

The PPT test sent every image call to one model. Image skills differ by the model they are
built on, so each call goes to the provider's model of the family the skill asked for: OpenAI
image models to gpt-image-2, Gemini image models (Nano Banana) to the same Gemini version, FLUX
to flux-2-pro. Skills reach the proxy in three formats: OpenAI's Images API, OpenAI's Responses
API with the image_generation tool, and Google's Gemini API (generateContent). Imagen's predict is not
routed: the provider's Imagen format is unverified, and a substitute model would put another model's
pictures under the skill's name.
"""
import base64
import re

OPENAI_IMAGE = "gpt-image-2"
FLUX_IMAGE = "flux-2-pro"
GEMINI_DEFAULT = "gemini-3.1-flash-image-preview"
# IMAGE_FORCE_NEWEST (owner, 2026-11-07): every call goes to the newest model of its family, whatever it
# names, so skills are compared on their prompts and workflow rather than on the model they pinned.
# The "-ext" channels bill per image (gpt-image-2.6-ext $0.0085, nano-banana-2.1-ext $0.012, 1K).
NEWEST = {"openai": "gpt-image-2.6-ext", "gemini": "gemini-nano-banana-2.1-ext", "flux": "flux-3-image"}
# Asked-for Gemini image model (substring, lowercase) -> the provider's model of that version.
GEMINI_IMAGE = (("3-pro", "gemini-3-pro-image-preview"), ("pro-image", "gemini-3-pro-image-preview"),
                ("nano-banana-pro", "gemini-3-pro-image-preview"), ("3.1", "gemini-3.1-flash-image-preview"),
                ("nano-banana-2", "gemini-3.1-flash-image-preview"), ("2.5", "gemini-2.5-flash-image-preview"))
# Aspect ratios the provider takes for Gemini and FLUX models (it rejects pixel sizes there).
RATIOS = ("1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9")
GEMINI_SIZES = {"1K", "2K", "4K"}


def is_gemini(model: str) -> bool:
    return model.startswith("gemini")


def is_flux(model: str) -> bool:
    return model.startswith("flux")


def family(asked: str | None) -> str:
    name = (asked or "").lower()
    if "flux" in name:
        return "flux"
    return "gemini" if any(k in name for k in ("gemini", "banana", "imagen")) else "openai"


def openai_model(asked: str | None, force: bool = False) -> str:
    """An OpenAI-format image call: FLUX if it asks for FLUX, Gemini if it asks for a Gemini
    image model (some MCP servers speak OpenAI's format to every backend), else gpt-image-2.
    With `force`, the newest model of that family."""
    if force:
        return NEWEST[family(asked)]
    name = (asked or "").lower()
    if "flux" in name:
        return FLUX_IMAGE
    if "gemini" in name or "banana" in name:
        return gemini_image_model(name)
    return OPENAI_IMAGE


def gemini_image_model(asked: str, force: bool = False) -> str:
    if force:
        return NEWEST["gemini"]
    name = asked.lower()
    return next((model for key, model in GEMINI_IMAGE if key in name), GEMINI_DEFAULT)


def is_gemini_image_call(model: str, body: dict) -> bool:
    """generateContent asks for an image when the model is an image model or the request
    asks for image output."""
    if any(k in model.lower() for k in ("image", "banana")):
        return True
    config = body.get("generationConfig") or body.get("generation_config") or {}
    modes = config.get("responseModalities") or config.get("response_modalities") or []
    return any(str(m).upper() == "IMAGE" for m in modes)


def ratio_for(size: str | None) -> str:
    """An OpenAI pixel size ("1536x1024") or a ratio ("16:9") as the nearest allowed ratio."""
    if not size or size == "auto":
        return "1:1"
    if size in RATIOS:
        return size
    m = re.match(r"^\s*(\d+)\s*[x:×]\s*(\d+)\s*$", str(size))
    if not m:
        return "1:1"
    want = int(m.group(1)) / int(m.group(2))
    return min(RATIOS, key=lambda r: abs(int(r.split(":")[0]) / int(r.split(":")[1]) - want))


def provider_body(model: str, prompt: str, size: str | None, images: list[str], resolution: str | None = None) -> dict:
    """The provider's request. Gemini takes a ratio plus 1K/2K/4K; FLUX 2 a ratio plus megapixels; FLUX 3
    and the GPT Image 2.5/2.6 channels a ratio (tried 11-07); gpt-image-2 also takes a pixel size."""
    body = {"model": model, "prompt": prompt, "n": 1}
    if is_gemini(model):
        body.update(size=ratio_for(size), resolution=resolution if resolution in GEMINI_SIZES else "1K")
    elif model.startswith("flux-3"):
        body.update(size=ratio_for(size))
    elif is_flux(model):
        body.update(size=ratio_for(size), resolution="1MP")
    elif model.startswith("gpt-image-2."):
        body.update(size=ratio_for(size), resolution="1k")
    else:
        body.update(size=size or "1:1")
    if images:
        body["image_urls"] = images
    return body


def _part_image(part: dict) -> str | None:
    blob = part.get("inlineData") or part.get("inline_data")
    if not blob or not blob.get("data"):
        return None
    mime = blob.get("mimeType") or blob.get("mime_type") or "image/png"
    return f"data:{mime};base64,{blob['data']}"


def gemini_request(body: dict) -> tuple[str, list[str], str, str]:
    """Prompt text, reference images (data URIs), ratio and size of a generateContent call."""
    texts, images = [], []
    for content in body.get("contents") or []:
        for part in (content.get("parts") if isinstance(content, dict) else None) or []:
            if part.get("text"):
                texts.append(part["text"])
            elif _part_image(part):
                images.append(_part_image(part))
    config = body.get("generationConfig") or body.get("generation_config") or {}
    image_cfg = config.get("imageConfig") or config.get("image_config") or {}
    ratio = image_cfg.get("aspectRatio") or image_cfg.get("aspect_ratio") or "1:1"
    size = str(image_cfg.get("imageSize") or image_cfg.get("image_size") or "1K").upper()
    return "\n\n".join(texts), images, ratio, size


def mime_of(b64: str) -> str:
    """The image type from its first bytes: providers return JPEG for some models whatever was asked."""
    head = base64.b64decode(b64[:24] + "=" * (-len(b64[:24]) % 4))
    if head.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


def gemini_response(images_b64: list[str], model: str) -> dict:
    parts = [{"inlineData": {"mimeType": mime_of(b), "data": b}} for b in images_b64]
    return {"candidates": [{"content": {"role": "model", "parts": parts}, "finishReason": "STOP", "index": 0}],
            "usageMetadata": {"promptTokenCount": 0, "candidatesTokenCount": 0, "totalTokenCount": 0},
            "modelVersion": model}


def _input_text(value) -> str:
    """The text of a Responses API `input`: a string, or messages whose content is text parts."""
    if isinstance(value, str):
        return value
    texts = []
    for item in value or []:
        content = item.get("content") if isinstance(item, dict) else None
        if isinstance(content, str):
            texts.append(content)
        for part in content if isinstance(content, list) else []:
            if isinstance(part, dict) and part.get("type") in ("input_text", "text"):
                texts.append(part.get("text", ""))
    return "\n\n".join(t for t in texts if t)


def responses_image_request(body: dict) -> tuple[str, str] | None:
    """Prompt and size when a Responses API call carries the image_generation tool, else None."""
    tool = next((t for t in body.get("tools") or [] if isinstance(t, dict) and t.get("type") == "image_generation"), None)
    if tool is None:
        return None
    return _input_text(body.get("input")), tool.get("size") or "1024x1024"


def responses_image(images_b64: list[str], model: str) -> dict:
    calls = [{"type": "image_generation_call", "id": f"ig_{i}", "status": "completed", "result": b}
             for i, b in enumerate(images_b64)]
    return {"id": "resp_sandbox", "object": "response", "status": "completed", "model": model,
            "output": calls, "output_text": ""}


def b64_of(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


GEMINI_LISTED = ("gemini-2.5-flash-image", "gemini-3-pro-image-preview", "gemini-3.1-flash-image-preview",
                 "gemini-2.5-flash", "gemini-3-flash-preview")
OPENAI_LISTED = ("gpt-image-1", "gpt-image-2", "dall-e-3", "flux-2-pro")


def model_list(path: str) -> dict | None:
    """GET answers for skills that list models before using one: Gemini's /v1beta/models[/<name>],
    OpenAI's /v1/models. None for any other path."""
    m = re.search(r"/v1(?:beta|alpha)?/models/([^/:]+)$", path)
    if m and "beta" in path:
        return {"name": f"models/{m.group(1)}", "supportedGenerationMethods": ["generateContent"]}
    if re.search(r"/v1(?:beta|alpha)/models$", path):
        return {"models": [{"name": f"models/{n}", "supportedGenerationMethods": ["generateContent"]} for n in GEMINI_LISTED]}
    if path.endswith("/v1/models"):
        return {"object": "list", "data": [{"id": n, "object": "model", "owned_by": "sandbox"} for n in OPENAI_LISTED]}
    return None
