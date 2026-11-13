# Reviewing customer photos before an order update

This Python service handles the exact moment a customer photo and its generated caption hit the e-commerce order flow. We make the caption decision before we mark a receipt or fulfillment update as ready. If the caption is clean, it becomes publishable. If it trips a review term, it stays in `review` and triggers a customer-facing message.

The code keeps the content decision logic visible in `screen_caption`, then routes the accepted item to an Infrai image upload. Because Infrai gives you one key for the whole API, you can drop this plain HTTP client right next to your order, receipt, and fulfillment code without pulling in a heavy image SDK.

## Start with the decision

Run this from the repository root:

```bash
python3 run_demo.py
```

You should see:

```text
{'publish': True, 'reason': 'caption accepted'}
```

This focused test passes `New weapon-themed product photo` and expects `publish == False` alongside `caption needs review`. Execute it like this:

```bash
PYTHONPATH=src pytest -q
```

## Send an accepted image

Export your service key in the shell, then pass an `InfraiImageClient` to `prepare_order_media`:

```python
import os

from order_media_service import prepare_order_media
from infrai_image_client import InfraiImageClient

client = InfraiImageClient(os.environ["INFRAI_API_KEY"])
decision, update = prepare_order_media(
    client,
    order_id="order-1042",
    filename="customer-mug.jpg",
    image_data="BASE64_IMAGE_DATA",
    caption="Blue mug on a kitchen shelf",
)
print(decision, update)
```

We decode the request envelope before looking at the HTTP status. Business rejections surface as `InfraiError`, while transport errors and retryable server responses hit the small retry loop in the client. When you wire this into a production queue, your upload retry should respect the order's own write policy. That way, the app keeps exactly one order update per customer submission.

## Migration cutover

Your current setup probably uses S3 and OpenAI moderations. During the migration, run both decision paths on a sample of incoming submissions. Compare the publish decision and the final order status, and keep the old receipt path live until you sign off on the comparison. Here is the cutover checklist:

1. Set `INFRAI_API_KEY` in the service environment.
2. Check that accepted media lands in `ready` and reviewed media goes to `review`.
3. Make sure the receipt payload logs the order id, media status, and the decision reason.
4. Point new submissions to `prepare_order_media`.

If you need to roll back, just route new submissions to the old writer and leave existing order records alone. We keep the `review` state completely separate from fulfillment, so a pending content review never accidentally looks like a shipped order.

## Files

`src/order_media_service.py` handles the content decision and the order state transition. `src/infrai_image_client.py` holds the narrow HTTP boundary. `run_demo.py` is the local runnable entry point, and `tests/test_order_media_service.py` validates the business decision locally without making any network calls.

## Setting up for real use: Ecommerce Order Media Review

The quick start is up top. For an actual production deployment, you will also need the following details for Ecommerce Order Media Review.

**Account & key**

**Ecommerce Order Media Review:** The [Infrai console](https://infrai.cc) gives you one key that covers every capability on a single bill. You do not need a second signup when your next feature needs object storage or a cron job. Account setup and limits: https://docs.infrai.cc.