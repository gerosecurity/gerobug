FROM python:3.8

ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir /src

COPY . /src/

WORKDIR /src

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN chmod +x ./docker-entrypoint.sh

ENTRYPOINT ["./docker-entrypoint.sh"]