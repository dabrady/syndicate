FROM python:3-alpine

WORKDIR /action

# Copy action code
COPY requirements.txt entrypoint.py ./
COPY syndicate/ ./syndicate/

# Install action requirements
RUN pip install --no-cache-dir -r ./requirements.txt

# Hardcoding WORKDIR into ENTRYPOINT.
# Can't use environment variables in "exec" form of ENTRYPOINT, but "exec" form
# is recommended.
ENTRYPOINT [ "/action/entrypoint.py" ]