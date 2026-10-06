"""Run the remaining frozen chronological stages sequentially, without retuning."""
import subprocess
import sys
from .phase3_engine import ROOT


def invoke(*args):
    subprocess.run([sys.executable,"-m",*args],check=True)


def main():
    if not (ROOT/"development/configuration-manifest.json").exists():
        raise ValueError("Complete feature recovery before starting final stages")
    if not (ROOT/"frozen-validation.json").exists():
        invoke("app.research.phase3_engine","--phase","development","--resume-generated")
    if not (ROOT/"development/development-completion.json").exists():invoke("app.research.phase3_reports")
    if not (ROOT/"validation-started.json").exists():
        invoke("app.research.phase3_engine","--phase","validation")
    elif not (ROOT/"validation/evaluation-complete.json").exists():
        raise ValueError("Validation already started but did not complete; never rerun automatically")
    invoke("app.research.phase3_reports","--phase","validation")
    invoke("app.research.phase3_status")


if __name__=="__main__":main()
