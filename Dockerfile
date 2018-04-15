FROM python:2.7
LABEL AUTHOR="SeaLife"

RUN mkdir /app

COPY . /tmp/minitor-bin/
COPY docker-assets/entrypoint.sh /root/entrypoint.sh

RUN chmod +x /root/entrypoint.sh

WORKDIR /tmp/minitor-bin

RUN pip install virtualenv tox yamlenv
RUN python setup.py build
RUN python setup.py install

WORKDIR /app

CMD [ "/root/entrypoint.sh" ]