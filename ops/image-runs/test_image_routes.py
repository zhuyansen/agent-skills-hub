"""Tests for ops/ppt-runs/sandbox/image_routes.py (model routing and formats of the image test).

Run: python3 -m pytest -q ops/image-runs/test_image_routes.py   (or python3 this file)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ppt-runs" / "sandbox"))
import image_routes as r  # noqa: E402


def test_openai_family_goes_to_gpt_image_2():
    assert r.openai_model("gpt-image-1") == "gpt-image-2"
    assert r.openai_model("dall-e-3") == "gpt-image-2"
    assert r.openai_model(None) == "gpt-image-2"


def test_other_families_keep_their_family():
    assert r.openai_model("flux-1.1-pro") == "flux-2-pro"
    assert r.openai_model("gemini-3-pro-image-preview") == "gemini-3-pro-image-preview"
    assert r.gemini_image_model("gemini-2.5-flash-image") == "gemini-2.5-flash-image-preview"
    assert r.gemini_image_model("nano-banana-pro-preview") == "gemini-3-pro-image-preview"
    assert r.gemini_image_model("gemini-3.1-flash-image-preview") == "gemini-3.1-flash-image-preview"
    assert r.gemini_image_model("some-new-image-model") == "gemini-3.1-flash-image-preview"


def test_pixel_sizes_become_the_nearest_ratio():
    assert r.ratio_for("1024x1024") == "1:1"
    assert r.ratio_for("1536x1024") == "3:2"
    assert r.ratio_for("1024x1536") == "2:3"
    assert r.ratio_for("1792x1024") == "16:9"
    assert r.ratio_for("16:9") == "16:9"
    assert r.ratio_for("auto") == "1:1"


def test_provider_body_by_family():
    g = r.provider_body("gemini-3-pro-image-preview", "a cat", "1024x1536", ["data:image/png;base64,AA"], "2K")
    assert g == {"model": "gemini-3-pro-image-preview", "prompt": "a cat", "n": 1, "size": "2:3",
                 "resolution": "2K", "image_urls": ["data:image/png;base64,AA"]}
    assert r.provider_body("gpt-image-2", "a cat", "1536x1024", [])["size"] == "1536x1024"
    assert r.provider_body("flux-2-pro", "a cat", None, [])["resolution"] == "1MP"


def test_gemini_request_both_spellings():
    body = {"contents": [{"role": "user", "parts": [{"text": "draw a bun"},
                                                     {"inline_data": {"mime_type": "image/jpeg", "data": "QUJD"}}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"], "imageConfig": {"aspectRatio": "3:4", "imageSize": "2k"}}}
    prompt, images, ratio, size = r.gemini_request(body)
    assert (prompt, images, ratio, size) == ("draw a bun", ["data:image/jpeg;base64,QUJD"], "3:4", "2K")
    assert r.is_gemini_image_call("gemini-2.5-flash", body)
    assert not r.is_gemini_image_call("gemini-2.5-flash", {"contents": []})
    assert r.is_gemini_image_call("gemini-3-pro-image-preview", {"contents": []})


def test_gemini_response_shape_and_type():
    png, jpeg = r.b64_of(b"\x89PNG\r\n\x1a\nrest"), r.b64_of(b"\xff\xd8\xff\xe0rest")
    out = r.gemini_response([png], "gemini-3-pro-image-preview")
    assert out["candidates"][0]["content"]["parts"][0] == {"inlineData": {"mimeType": "image/png", "data": png}}
    assert r.mime_of(jpeg) == "image/jpeg"


def test_responses_api_image_tool():
    body = {"model": "gpt-5", "input": [{"role": "user", "content": [{"type": "input_text", "text": "a poster"}]}],
            "tools": [{"type": "image_generation", "size": "1024x1536"}]}
    assert r.responses_image_request(body) == ("a poster", "1024x1536")
    assert r.responses_image_request({"input": "hi", "tools": []}) is None
    assert r.responses_image(["AAA"], "gpt-image-2")["output"][0]["result"] == "AAA"


def test_model_lists_for_get():
    assert r.model_list("/v1beta/models")["models"][0]["name"].startswith("models/gemini")
    assert r.model_list("/v1beta/models/gemini-3-pro-image-preview")["name"] == "models/gemini-3-pro-image-preview"
    assert r.model_list("/v1/models")["data"][1]["id"] == "gpt-image-2"
    assert r.model_list("/v1/images/generations") is None


def test_force_newest_by_family():
    assert r.openai_model("gpt-image-1", force=True) == "gpt-image-2.6-ext"
    assert r.openai_model("dall-e-3", force=True) == "gpt-image-2.6-ext"
    assert r.openai_model("flux-1.1-pro", force=True) == "flux-3-image"
    assert r.openai_model("gemini-3-pro-image-preview", force=True) == "gemini-nano-banana-2.1-ext"
    assert r.gemini_image_model("gemini-3-pro-image-preview", force=True) == "gemini-nano-banana-2.1-ext"


def test_newest_channels_take_a_ratio():
    assert r.provider_body("gpt-image-2.6-ext", "x", "1024x1536", [])["size"] == "2:3"
    assert r.provider_body("gpt-image-2.6-ext", "x", "1024x1536", [])["resolution"] == "1k"
    assert "resolution" not in r.provider_body("flux-3-image", "x", "16:9", [])
    assert r.provider_body("gemini-nano-banana-2.1-ext", "x", "3:4", [], "2K")["resolution"] == "2K"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
