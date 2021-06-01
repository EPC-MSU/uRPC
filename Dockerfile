FROM python:3.6-alpine

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 8888
CMD ["python", "main.py"]
