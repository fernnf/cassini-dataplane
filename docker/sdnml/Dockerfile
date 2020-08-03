FROM odtn/odtn-cassini:latest

COPY ./ /root/transponder-cassini

ENV PYTHONPATH=/root/transponder-cassini/

RUN chmod +x /root/transponder-cassini/docker/sdnml/init-service.sh

CMD ["/root/transponder-cassini/docker/sdnml/init-service.sh"]