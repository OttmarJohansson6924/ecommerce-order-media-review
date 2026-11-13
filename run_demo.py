from order_media_service import screen_caption


if __name__ == "__main__":
    decision = screen_caption("Blue mug on a kitchen shelf")
    print({"publish": decision.publish, "reason": decision.reason})
