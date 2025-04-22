FROM python

WORKDIR /app

COPY . /app
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8000", "server:app"]