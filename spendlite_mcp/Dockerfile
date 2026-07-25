FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Bake the seeded database into the image. Fine for a demo: the data is
# generated, identical on every build, and nobody writes to it at runtime.
ENV SPENDLITE_DB_PATH=/app/expenses.db
RUN python seed.py

EXPOSE 8010
CMD ["python", "server.py"]
