FROM python:3.11-slim

RUN mkdir /timeassist
WORKDIR /timeassist
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src /timeassist/src/

CMD ["python", "./src/main.py"]