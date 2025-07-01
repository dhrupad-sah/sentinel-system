FROM python:3.10-slim

WORKDIR /project

RUN pip install -U pdm

ENV PDM_CHECK_UPDATE=false

COPY pyproject.toml pdm.lock README.md ./
RUN pdm install --check --prod --no-editable

COPY . .

# Command to run the application
CMD pdm run start