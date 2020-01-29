FROM python:3-alpine

WORKDIR /action

# Copy action metadata
COPY LICENSE README.md requirements.txt ./
# Copy action code
COPY entrypoint.sh ./
COPY src/ ./src/

# Install action requirements
RUN pip install --no-cache-dir -r ./requirements.txt

# Hardcoding WORKDIR into ENTRYPOINT.
# Can't use environment variables in "exec" form of ENTRYPOINT, but "exec" form
# is recommended.
ENTRYPOINT [ "/action/entrypoint.sh" ]