import sys
import atheris

def TestOneInput(data):
    if len(data) > 3 and data[0] == ord("F"):
        if data[1] == ord("U"):
            if data[2] == ord("Z"):
                if data[3] == ord("Z"):
                    raise RuntimeError("crash found")

atheris.instrument_all()
atheris.Setup(sys.argv, TestOneInput)
atheris.Fuzz()