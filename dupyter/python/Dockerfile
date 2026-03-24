FROM python:PY_VER-slim

ARG UID
ARG GID
ARG USERNAME

RUN apt-get update \
    && apt-get install -y --no-install-recommends git wget nano \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g ${GID} ${USERNAME} \
    && useradd -m -u ${UID} -g ${GID} -G root ${USERNAME}

ENV PATH="/home/${USERNAME}/.local/bin:$PATH"

USER ${USERNAME}

RUN sed -i 's/^#force_color_prompt=yes/force_color_prompt=yes/' /home/${USERNAME}/.bashrc

CMD ["bash"]
