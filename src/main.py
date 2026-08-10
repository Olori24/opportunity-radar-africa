from src.logging import configure_logging


logger = configure_logging()


def main():

    logger.info(
        "Opportunity Radar Africa started."
    )

    print("=" * 40)
    print("Opportunity Radar Africa")
    print("Status: healthy")
    print("=" * 40)


if __name__ == "__main__":
    main()
