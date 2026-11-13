from order_media_service import screen_caption
from infrai_image_client import infrai_image_upload


def test_caption_with_review_term_stays_out_of_publish_queue():
    decision = screen_caption("New weapon-themed product photo")

    assert decision.publish is False
    assert decision.reason == "caption needs review"


def test_clean_caption_is_ready_to_publish():
    decision = screen_caption("Blue mug on a kitchen shelf")

    assert decision.publish is True


def test_image_upload_preserves_all_identifiers():
    class Client:
        def upload(self, image_data, filename):
            return {"data": {"id": "image-1", "image": "https://example/image-1"}}

    assert infrai_image_upload(Client(), "data", "image.png") == (
        "image-1",
        "https://example/image-1",
    )
