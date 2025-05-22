FROM ubuntu:latest
LABEL maintainer="ETSI CTI - cti_support@etsi.org"

ENV TZ=Europe/Paris
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update -y \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y \
  	 locales \
     python3-pip \
     python3-dev \
     build-essential \
     python3-tosca-parser \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip

RUN sed -i 's/^# *\(en_US.UTF-8\)/\1/' /etc/locale.gen && locale-gen

RUN echo "export LC_ALL=en_US.UTF-8" >> ~/.bashrc
RUN echo "export LANG=en_US.UTF-8" >> ~/.bashrc
RUN echo "export LANGUAGE=en_US.UTF-8" >> ~/.bashrc

COPY /src /app
COPY requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8

RUN mkdir /app/upload

ENTRYPOINT ["python3"]
CMD ["web_app.py"]
