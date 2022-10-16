import httpx

from routes import crfpp

MODEL_URL = "https://github.com/mealie-recipes/nlp-model/releases/download/v1.0.0/model.crfmodel"


def main():
    """
    Install the model into the crfpp directory
    """
    with httpx.stream("GET", MODEL_URL, follow_redirects=True) as r:
        with open(crfpp.MODEL_PATH, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)


if __name__ == "__main__":
    main()
