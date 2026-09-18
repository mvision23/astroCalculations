"""Compatibility launcher for the original script path.

The original 12 workflows now live in astrocalc.calculations and the terminal
menu in astrocalc.ui. The historical implementation remains in git at
8babf9e6f150ad4d90e902ec915f4f5727dc3dd2; it is not run on import.
"""

if __name__ == "__main__":
    from astrocalc.__main__ import main
    main()
