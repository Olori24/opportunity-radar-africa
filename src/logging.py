from logging import getLogger, basicConfig, INFO


def configure_logging():
    basicConfig(
        level=INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return getLogger("opportunity-radar-africa")


logger = configure_logging()


def main():
    logger.info("Opportunity Radar Africa started.")

    print("=" * 40)
    print("Opportunity Radar Africa")
    print("Status: healthy")
    print("=" * 40)


if __name__ == "__main__":
    main()
