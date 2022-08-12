# This Dockerfile creates a dev environment for covid19
# To build it run: docker build --no-cache -t covid19 .;
# To run it run: docker run -it --rm --name covid19dev covid19 /bin/bash; 
# To do both: docker build --no-cache -t covid19 .; docker run -it --rm --name covid19dev covid19 /bin/bash;  
# Or just run in this directory ./build-and-run.sh
# Sidenote: added --no-cache to build, so that the git clone always gets the latest covid repo

# use python3.9 base build
FROM python:3.9
MAINTAINER bhbmaster@gmail.com

# prepare for developing
RUN apt-get update && apt-get install vim -y

# prepare git settings (to none bhbmaster, change these values if planning to make your own commits)
RUN git config --global user.name bhbmaster
RUN git config --global user.email bhbmaster@gmail.com

# prepare covid19 dir
WORKDIR /covid19
RUN git clone https://github.com/bhbmaster/covid19.git ./
RUN pip install -r requirements.txt
RUN echo "Last docker built on `date`" > dev-docker-env/last-docker-build.txt
           
# (commented out because no need to run below, as we will remember to run git pull from within docker)              
# when entering container, run git pull                       
# CMD ["git", "pull"]
# CMD ["sh", "-c", "git pull > test.out; pwd >> test.out; date >> test.out;"]
