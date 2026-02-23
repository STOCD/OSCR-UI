FROM python:3.14-trixie

RUN apt-get update
RUN apt-get install -y binutils
RUN apt-get install -y libopencv-dev
RUN apt-get install -y python3-opencv
RUN apt-get install -y libxcb-cursor0

RUN mkdir /build
COPY ./ /build/
WORKDIR /build
