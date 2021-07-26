FROM tiangolo/uvicorn-gunicorn-fastapi:latest

ENV PYTHONPATH "${PYTHONPATH}:/"

# Install Poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy using poetry.lock* in case it doesn't exist yet
COPY ./pyproject.toml ./poetry.lock* /app/

RUN poetry install --no-root --no-dev
RUN python -m pip install --upgrade apteryx

COPY ./app /app

#install poppler (for pdf2image)
RUN apt-get clean
RUN apt-get update
RUN apt-get install poppler-utils -y

#Install tesseract (for pytesseract OCR)
RUN apt install tesseract-ocr -y
RUN apt install libtesseract-dev -y