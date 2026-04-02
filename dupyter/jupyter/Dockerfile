FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    JUPYTER_PORT=8888 \
    JUPYTER_DIR=/opt/jupyter

RUN useradd -ms /bin/bash jovian

WORKDIR ${JUPYTER_DIR}

# Some basic stuff
COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt && \
    mkdir -p ${JUPYTER_DIR}/workspace && \
    chown -R jovian:jovian ${JUPYTER_DIR}

USER jovian

EXPOSE ${JUPYTER_PORT}

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--ServerApp.root_dir=/opt/jupyter/workspace"]