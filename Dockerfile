FROM python:3.9.12-slim

WORKDIR /usr/src
COPY requirements.txt .
RUN pip --no-cache install -r requirements.txt

COPY app.py .
COPY templates templates

CMD ["python3", "./app.py"]