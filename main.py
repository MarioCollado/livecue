"""Punto de entrada principal de LiveCue."""

from app.bootstrap import main


if __name__ == "__main__":
    import sys

    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback

        traceback.print_exc()
        input("\nPresiona Enter para salir...")
        sys.exit(1)
