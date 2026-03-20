"""AniUpscale entry point."""
from app import AniUpscaleApp


def main() -> None:
    app = AniUpscaleApp()
    app.mainloop()


if __name__ == "__main__":
    main()
