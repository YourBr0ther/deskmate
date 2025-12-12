"""Entry point for running DeskMate as a module."""

from deskmate.app import create_app


def main() -> None:
    """Main entry point."""
    app = create_app()
    app.run()


if __name__ == "__main__":
    main()
