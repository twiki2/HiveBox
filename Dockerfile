FROM python:3.13.1

WORKDIR /app

COPY  requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

COPY main.py .

EXPOSE 5000

CMD ["python","main.py"]