#!/bin/bash

docker run --gpus all --name cap-gen --network deeverse_proxy --env-file .env -d -p 8000:8000 xuanminator/caption-gen:1.0
