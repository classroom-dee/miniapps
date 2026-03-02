#!/bin/bash

# Constants
CONTEXT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURR_DIR=$(pwd)
CONT_PATH="/workspace"

# Defaults
PROJECT_PATH=""
COMMAND=""
SCRIPT_PATH=""
ARGUMENTS=""
CERT=""
PY_VER="3.11"
IMG_NAME="python${PY_VER}_service:latest"
DOTENV=""
NETWORK="bridge"
REQUIREMENTS_FILE=""
INTERACTIVE=false

# Docker arg defaults
REQ_DOCKER_ARG=""
SCRIPT_DOCKER_ARG=""
INTERACTIVE_ARG=""
# Bind mounts
REQ_DOCKER_VOL=""
ENV_DOCKER_VOL=""
CERT_DOCKER_VOL=""
SCRIPT_DOCKER_VOL=""
PROJ_DOCKER_VOL=""

# No args handling
if [[ $# -eq 0 ]]; then
    "$0" --help
    exit 1
fi

# Dashed args parsing
while [[ $# -gt 0 ]]; do
    case "$1" in
        -p|--project-path)
            PROJECT_PATH="$2"
            shift 2
            ;;
        --cmd|--command)
            COMMAND="$2"
            shift 2
            ;;
        -s|--script-path)
            SCRIPT_PATH="$2"
            shift 2
            ;;
        --args|--arguments)
            ARGUMENTS="$2"
            shift 2
            ;;
        -c|--certificate)
            CERT="$2"
            shift 2
            ;;
        -v|--python-version) 
            PY_VER="$2"
            shift 2
            ;;
        -e|--dotenv)
            DOTENV="$2"
            shift 2
            ;;
        -n|--network)
            NETWORK="$2"
            shift 2
            ;;
        -r|--requirements)
            REQUIREMENTS_FILE="$2"
            shift 2
            ;;
        --i|--interactive)
            INTERACTIVE=true
            shift
            ;;
        -h|--help) 
            echo "----------------------prs version 0.1------------------------"
            echo "Usage: prs [options]"
            echo "  -p, --project-path       Path to project"
            echo "  --cmd, --command         Command(s) to run on container"
            echo "  -s, --script-path        Path to script"
            echo "  --args, --arguments      Python script args to pass"
            echo "  -c, --certificate        Certificate file"
            echo "  -v, --python-version     Python version"
            echo "  -e, --dotenv             .env file path"
            echo "  -n, --network            Docker network"
            echo "  -r, --requirements       Requirements file"
            echo "  --i, --interactive       Run in interactive mode"
            echo "  -h, --help               Show help"
            echo "-------------------------------------------------------------"
            echo "If -p is specified, --cmd becomes eligible(Don't forget the double quotes), -"
            echo "and --i can be flagged for a detached interactive session."
            echo "BTST, --args is available for -s, and this will run the script, terminate the session."
            echo "-p and -s are mutually exclusive and --i cannot be used for -s!"
            exit 0
            ;;
        -*)
            echo "Invalid option: $1"
            exit 1
            ;;
        *) 
            break
            ;;
    esac
done

# Exclusion zone
if [[ -z "$PROJECT_PATH" && -z "$SCRIPT_PATH" ]]; then
    echo -e "\033[38;5;160mYou must specify one of -p and -s!\033[0m" >&2
    exit 1
fi
if [[ -n "$PROJECT_PATH" && -n "$SCRIPT_PATH" ]]; then
    echo -e "\033[38;5;160m-p and -s are mutually exclusive!\033[0m" >&2
    exit 1
fi
if [[ -n "$COMMAND" && -z "$PROJECT_PATH" ]]; then
    echo "\033[38;5;160m--cmd can only be used with -p!\033[0m" >&2
    exit 1
fi
if [[ -n "$ARGS" && -z "$SCRIPT_PATH" ]]; then
    echo "\033[38;5;160m--args can only be used with -s!\033[0m" >&2
    exit 1
fi
if [[ "$INTERACTIVE" == true && -n "$SCRIPT_PATH" ]]; then
    echo "\033[38;5;160m--i cannot be used with -s!\033[0m" >&2
    exit 1
fi
echo -e "Arguments check \033[38;5;40mpassed...\033[0m"

# Paths validation & dynamic arguments
if [[ -n "$SCRIPT_PATH" ]]; then
    if [[ -f $(realpath "$SCRIPT_PATH") ]]; then
        SCRIPT_PATH=$(realpath "$SCRIPT_PATH")
        SCRIPT_CONT_PATH=$CONT_PATH/$(basename "$SCRIPT_PATH")
        SCRIPT_DOCKER_ARG=" python $SCRIPT_CONT_PATH $ARGUMENTS "
        SCRIPT_DOCKER_VOL="-v $SCRIPT_PATH:$SCRIPT_CONT_PATH"
    else
        echo "Invalid script file path $(realpath $SCRIPT_PATH)"
        exit 1
    fi
fi
if [[ -n "$PROJECT_PATH" ]]; then
    if [[ -d $(realpath "$PROJECT_PATH") ]]; then
        PROJECT_PATH=$(realpath "$PROJECT_PATH")
        PROJ_DOCKER_VOL="-v $PROJECT_PATH:$CONT_PATH/$(basename "$PROJECT_PATH")"
    else
        echo "Invalid project path."
        exit 1
    fi
fi
if [[ -n "$CERT" ]]; then
    if [[ -f $(realpath "$CERT") ]]; then
        CERT=$(realpath "$CERT")
        CERT_DOCKER_VOL="-v $CERT:$CONT_PATH/$(basename "$CERT")"
    else
        echo "Invalid certificate path."
        exit 1
    fi
fi
if [[ -n "$DOTENV" ]]; then
    if [[ -f $(realpath "$DOTENV") ]]; then
        DOTENV=$(realpath "$DOTENV")
        ENV_DOCKER_VOL="-v $DOTENV:$CONT_PATH/$(basename "$DOTENV")"
    else
        echo "Invalid .env path."
        exit 1
    fi
fi
if [[ -n "$REQUIREMENTS_FILE" ]]; then
    if [[ -f $(realpath "$REQUIREMENTS_FILE") ]]; then
        REQUIREMENTS_FILE=$(realpath "$REQUIREMENTS_FILE")
        REQ_DOCKER_ARG=" pip install -r $REQUIREMENTS_FILE --quiet --root-user-action=ignore --disable-pip-version-check --no-cache-dir && "
        REQ_DOCKER_VOL="-v $REQUIREMENTS_FILE:$CONT_PATH/$(basename "$REQUIREMENTS_FILE")"
    else
        echo "Invalid requirement file path."
        exit 1
    fi
fi
if [[ "$INTERACTIVE" == true ]]; then
    INTERACTIVE_ARG="-it"
    if [[ -z "$COMMAND" ]]; then
        COMMAND="/bin/bash"
    fi
fi
echo -e "Paths check and args setup \033[38;5;40mpassed...\033[0m"

# Image check, run
if docker image inspect "${IMG_NAME}" > /dev/null 2>&1; then
    echo "Image exists. Running..."
else
    echo "Image does not exist. Building..."
    sed -i "s|python:PY_VER-slim|python:${PY_VER}-slim|" "$CONTEXT"/Dockerfile
    docker build \
        --build-arg UID=$(id -u) \
        --build-arg GID=$(id -g) \
        --build-arg USERNAME=$(whoami) \
        -t "${IMG_NAME}" \
        "${CONTEXT}" || exit 1
    sed -i "s|python:${PY_VER}-slim|python:PY_VER-slim|" "$CONTEXT"/Dockerfile
fi

docker run ${INTERACTIVE_ARG} --rm \
    --network "${NETWORK}" \
    --add-host host.docker.internal:host-gateway \
    ${SCRIPT_DOCKER_VOL} \
    ${REQ_DOCKER_VOL} \
    ${ENV_DOCKER_VOL} \
    ${CERT_DOCKER_VOL} \
    ${PROJ_DOCKER_VOL} \
    -w "${CONT_PATH}" \
    "${IMG_NAME}" \
    "${REQ_DOCKER_ARG} ${SCRIPT_DOCKER_ARG} ${COMMAND}"