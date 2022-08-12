# This Dockerfile creates a dev environment for covid19
# To build it run: docker build -t covid19 .;
# To run it run: docker run -it --rm --name covid19test covid19 /bin/bash;
# To do both: docker build -t covid19 .; docker run -it --rm --name covid19test covid19 /bin/bash;

# use python3.9 base build
FROM python:3.9
MAINTAINER bhbmaster@gmail.com

# prepare for developing
RUN apt-get update && apt-get install vim -y

# prepare git settings
RUN git config --global user.name bhbmaster
RUN git config --global user.email bhbmaster@gmail.com

# prepare covid19 dir
WORKDIR /covid19
RUN git clone https://github.com/bhbmaster/covid19.git ./
RUN echo "Last docker built on `date`" > last-docker-build.txt
