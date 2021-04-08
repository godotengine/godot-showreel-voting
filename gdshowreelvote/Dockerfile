FROM python:3
ENV PYTHONUNBUFFERED 1

WORKDIR /www/gdshowreel

# Install pip dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install daphne

# Copy the remaining files
COPY . .

# Collect the static files
RUN mkdir -p /var/www/showreel.godotengine.org/static/

# Warning: we collect the statics at runtime and not at build time.
# As docker-compose does not support build time secrets SECRET_KEY
# cannot be set at build time, while it is needed for this operation
CMD python ./manage.py collectstatic --clear --noinput; daphne -b 0.0.0.0 -p 8000 gdshowreelvote.asgi:application