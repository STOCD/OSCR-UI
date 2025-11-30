FROM debian:trixie

RUN apt-get update
RUN apt-get install -y binutils
RUN apt-get install -y python3.13
RUN ln -s /usr/bin/python3.13 /usr/bin/python3
RUN apt-get install -y python3.13-venv
RUN apt-get install -y python3.13-dev
RUN apt-get install -y libopencv-dev
RUN apt-get install -y python3-opencv
RUN apt-get install -y libxcb-cursor0

RUN mkdir /build
COPY ./ /build/
WORKDIR /build
