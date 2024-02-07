"""
    Setup file for fluidcalcs.
    Use setup.cfg to configure your project.
"""

from setuptools import setup

if __name__ == "__main__":
    try:
        setup(use_scm_version={"version_scheme": "no-guess-dev"})
    except LookupError:
        print(
            "\n\nAn error occurred while building the project, "
            "setuptools-scm may not have been able to detect version."
            "Setting to 0.0.0 \n\n"
        )
        setup(version="0.0.0")
    except:  # noqa
        print(
            "\n\nAn error occurred while building the project, "
            "please ensure you have the most updated version of setuptools, "
            "setuptools_scm and wheel with:\n"
            "   pip install -U setuptools setuptools_scm wheel\n\n"
        )
        raise
