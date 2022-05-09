FROM lsiobase/alpine:3.15

# environment variables
ENV PYTHONUNBUFFERED=1
#ENV DJANGO_SETTINGS_MODULE=plaxt.settings

# install packages
RUN \
    echo "**** install packages ****" && \
    apk add --no-cache \
        python3 \
        py3-pip

# setup working directory
#RUN mkdir /app
WORKDIR /app

# add project files
ADD project/ /app/

# install python modules
RUN \
    echo "**** install python modules ****" && \
    pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# cleanup
RUN \
    echo "**** cleanup ****" && \
    rm -rf \
        /tmp/*

# add local files
ADD root/ /

# ports and volumes
EXPOSE 8000/tcp
VOLUME /config
