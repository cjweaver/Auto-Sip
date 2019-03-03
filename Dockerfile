FROM salimfadhley/testpython as salpython
COPY . /project
RUN python -m pip install -e /project/src
RUN useradd -u 1000 python
WORKDIR /home/python
USER python
