FROM sdnm/odtn-cassini:latest

COPY ./ /root/transponder-cassini

ENV PYTHONPATH /root/transponder-cassini/

RUN chmod +x /root/transponder-cassini/docker/sdnm/init-service.sh

CMD ["/root/transponder-cassini/docker/sdnm/init-service.sh"]