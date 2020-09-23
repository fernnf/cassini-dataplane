FROM odtn/odtn-cassini:latest

COPY ./ /root/transponder-cassini

ENV PYTHONPATH /root/transponder-cassini/

RUN chmod +x /root/transponder-cassini/docker/sdnm/init-service.sh

ENV RUNNING '0'

CMD ["/root/transponder-cassini/docker/sdnm/init-service.sh"]