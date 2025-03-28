FROM python:3.13-alpine3.21

WORKDIR /app

COPY  requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 5000

CMD ["python","main.py"]