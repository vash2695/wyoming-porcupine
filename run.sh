#!/usr/bin/env bash
set -e

# Get arguments from options
uri=$(jq -r '.uri // "tcp://0.0.0.0:10400"' /data/options.json)
access_key=$(jq -r '.access_key // ""' /data/options.json)
sensitivity=$(jq -r '.sensitivity // 0.5' /data/options.json)
language=$(jq -r '.language // "en"' /data/options.json)

# Require access key
if [[ -z "${access_key}" ]]; then
    echo "Missing access_key option. Get one from https://console.picovoice.ai/"
    exit 1
fi

# Configure logging
log_level=INFO
if [[ -n "${ADDON_DEBUG}" && "${ADDON_DEBUG}" = "true" ]]; then
    log_level=DEBUG
    debug_arg="--debug"
fi

echo "Starting Porcupine with URI ${uri} (language=${language}, sensitivity=${sensitivity})"

# Run porcupine
exec wyoming-porcupine3 \
    --uri "${uri}" \
    --access-key "${access_key}" \
    --sensitivity "${sensitivity}" \
    --language "${language}" \
    ${debug_arg} \
    --log-format "%(levelname)s:%(asctime)s:%(name)s: %(message)s" 