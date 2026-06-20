FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=5000
EXPOSE 5000

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python"]
CMD [ "app.py" ]
