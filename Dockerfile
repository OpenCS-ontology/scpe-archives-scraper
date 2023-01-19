FROM python:3.10.9-slim-bullseye

# Packages. binutils needed for pyinstaller
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y binutils

# Setting virtual env (https://pythonspeed.com/articles/activate-virtualenv-dockerfile/)
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /
COPY src/ ./

RUN pip3 install wheel && \
    pip3 install -r requirements.txt

RUN pyinstaller -F main.py

# Cleanup
RUN mv dist/main ./ && \
    rmdir dist && \
    rm -r build && \
    rm main.spec && \
    rm *.py

ENV SCRAPER_DEST_DIR=/target
CMD ["./main"]
