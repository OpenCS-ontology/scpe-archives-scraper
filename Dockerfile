FROM alpine:3.17.1

WORKDIR /
COPY main /main
ENV SCRAPER_DEST_DIR=/target

CMD /main